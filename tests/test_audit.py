"""Regression tests independent of the original portfolio's test suite."""
import sys, math, unittest
from pathlib import Path
from dataclasses import replace
import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.special import erf
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from atmosphere import (DB_LABEL,PAPER_EXPONENTIAL,scenarios_1550nm,exact_distribution,
    path_lengths_km,transmittance_from_q,loss_db_from_q,effective_transmittance,
    exact_statistics,mean_transmittance_factorized,radiation_fog_db_per_km)
from fso_link import (Link, DEFAULT_PRIOR, gaussian_aperture_capture, availability,
    conditional_availability, min_aperture_for_target, worst_case_tv_greedy,
    worst_case_tv_lp, weather_limited_ceiling, sample_link, success_probability_for_transmittance)

# Independent Table II fixtures, checked against arXiv:2604.18207v1, Table II
# and Section IV-A (cloud placement). Units reproduce printed values.
FIXTURES={
'clear':[(0,3,[(1,.034)]),(3,15,[(1,.0025)])],
'pollution':[(0,3,[(.7,.3536),(.3,.034)]),(3,15,[(1,.0025)])],
'fog':[(0,1,[(1,1.768)]),(1,2,[(1,.4592)]),(2,15,[(1,.0025)])],
'rain':[(0,.6,[(1,.0025)]),(.6,1.4,[(.9,8.2425),(.1,.034)]),(1.4,15,[(1,.0025)])],
'snow':[(0,2,[(1,.2)]),(2,15,[(1,.0025)])]}
VOLCANIC=(15,30,[(.5,.0104),(.5,.0002036)])
# Hand-computed 3km integrated printed attenuation and probability pairs.
REF=[[(.102,1)],[(1.0608,.7),(.102,.3)],[(2.2297,1)],[(6.5995,.9),(.0327,.1)],[(.4025,1)]]

def independent_capture(a,w,r):
    # Cartesian slicing, not Bessel integration or noncentral chi-squared CDF.
    scale=math.sqrt(2)/w
    def f(x):
        y=math.sqrt(max(0.,a*a-x*x))
        return math.sqrt(2/math.pi)/w*math.exp(-2*((x-r)/w)**2)*erf(scale*y)
    return quad(f,-a,a,epsabs=2e-12,epsrel=2e-11)[0]

def independent_probability(a,j,link,rho):
    # Independent state fixture, explicit power convention, Cartesian integral.
    w=math.hypot(.025,55e-6*3000);sd=j*1e-6*3000
    vec=[]
    for states in REF:
        p=0.
        for q,prob in states:
            t=10**(-q/10) if link.convention==DB_LABEL else math.exp(-q)
            needed=2/(35*t)
            if needed>=independent_capture(a,w,0): continue
            rc=brentq(lambda r: independent_capture(a,w,r)-needed,0,a+10*w,xtol=1e-12)
            p+=prob*(-math.expm1(-rc**2/(2*sd**2)))
        vec.append(p)
    return worst_case_tv_lp(vec,np.array([.76,.10,.07,.04,.03]),rho)

class AuditChecks(unittest.TestCase):
    def test_source_fixture_all_layers(self):
        for name,expected in FIXTURES.items():
            actual=[(l.bottom_km,l.top_km,[(s.probability,s.printed_coefficient_per_km) for s in l.states]) for l in scenarios_1550nm()[name].layers]
            self.assertEqual(actual,expected+[VOLCANIC])
    def test_reference_state_values(self):
        for name,expected in zip(('clear','pollution','fog','rain','snow'),REF):
            q,p=exact_distribution(scenarios_1550nm()[name],3)
            np.testing.assert_allclose(q,[x[0] for x in expected],atol=1e-12)
            np.testing.assert_allclose(p,[x[1] for x in expected],atol=1e-12)
    def test_db_unit_conversion(self):
        self.assertEqual(Link().convention,DB_LABEL)
        self.assertAlmostEqual(transmittance_from_q(10),.1)
        self.assertAlmostEqual(transmittance_from_q(3),10**(-.3))
        self.assertAlmostEqual(float(loss_db_from_q(2,PAPER_EXPONENTIAL)),20/math.log(10))
    def test_layer_geometry_boundaries(self):
        for name,s in scenarios_1550nm().items():
            for h in [0,.3,.6,1,1.4,2,3,15,20,30]:
                for z in [0,30,70]:
                    self.assertAlmostEqual(sum(path_lengths_km(s,h,z)),h/math.cos(math.radians(z)),places=10)
    def test_jensen_and_factorization(self):
        for name,s in scenarios_1550nm().items():
            for conv in [DB_LABEL,PAPER_EXPONENTIAL]:
                result=exact_statistics(s,25,45,convention=conv)
                self.assertGreaterEqual(result['mean_transmittance']+1e-14,result['effective_transmittance'])
                self.assertAlmostEqual(result['mean_transmittance'],mean_transmittance_factorized(s,25,45,conv),places=12)
    def test_prose_and_fog_stress(self):
        q,p=exact_distribution(scenarios_1550nm('clear_prose')['clear'],3)
        self.assertAlmostEqual(q[0],.0075)
        self.assertAlmostEqual(radiation_fog_db_per_km(.2),(10/math.log(10))*(.18126*1.55**2+.13709*1.55+3.7502)/.2)
        q,p=exact_distribution(scenarios_1550nm('fog_visibility_stress')['fog'],3)
        self.assertGreater(q[0],20)
        with self.assertRaises(ValueError): Link(profile='fog_visibility_stress',convention=PAPER_EXPONENTIAL)
    def test_cartesian_aperture(self):
        for a,w,r in [(.025,.16688,0),(.1,.2,.07),(.14,.17,.25),(.25,.18,.3)]:
            self.assertAlmostEqual(float(gaussian_aperture_capture(a,w,r)),independent_capture(a,w,r),places=10)
    def test_independent_reference_design(self):
        for conv in [DB_LABEL,PAPER_EXPONENTIAL]:
            l=Link(convention=conv)
            for rho in [0,.04,.08]:
                a=min_aperture_for_target(.92,15,l,rho=rho)
                if math.isfinite(a):
                    self.assertGreaterEqual(availability(a,15,l,rho=rho),.92)
                    self.assertAlmostEqual(independent_probability(a,15,l,rho),.92,delta=4e-6)
                    self.assertLess(independent_probability(a-2e-7,15,l,rho),.92)
                else: self.assertLess(weather_limited_ceiling(l,rho=rho)[0],.92)
    def test_zero_jitter_step_boundary(self):
        l=Link();a=min_aperture_for_target(.92,0,l)
        self.assertGreaterEqual(availability(a,0,l),.92)
        self.assertLess(availability(a-2e-7,0,l),.92)
    def test_exact_threshold_equality(self):
        # 35 mW equals the *unattenuated* limiting power. Finite Gaussian capture < 1.
        l=replace(Link(),threshold_mw=35.)
        self.assertEqual(success_probability_for_transmittance(1,.5,0,l),0.)
        self.assertEqual(success_probability_for_transmittance(1,.5,15,l),0.)
        self.assertEqual(weather_limited_ceiling(l)[0],0.)
    def test_bracket_tiny_negative_upper_residual(self):
        l=Link();hi=.08;t=availability(hi,15,l)+1e-10
        self.assertTrue(math.isnan(min_aperture_for_target(t,15,l,a_hi=hi)))
    def test_nonfinite_inputs(self):
        for bad in [float('nan'),float('inf')]:
            with self.assertRaises(ValueError): gaussian_aperture_capture(.1,.1,bad)
            with self.assertRaises(ValueError): success_probability_for_transmittance(bad,.1,15,Link())
            with self.assertRaises(ValueError): worst_case_tv_greedy([bad,0,0,0,0],DEFAULT_PRIOR,.04)
            with self.assertRaises(ValueError): sample_link(100,.1,bad,Link())
        with self.assertRaises(ValueError): sample_link(1,.1,15,Link())
        with self.assertRaises(ValueError): Link(divergence_urad=1.)
    def test_weather_ceiling_stress(self):
        l=Link(profile='fog_visibility_stress')
        self.assertAlmostEqual(weather_limited_ceiling(l)[0],.93)
        self.assertAlmostEqual(weather_limited_ceiling(l,rho=.04)[0],.89)
        self.assertTrue(math.isnan(min_aperture_for_target(.92,15,l,rho=.04)))
    def test_tv_extremes(self):
        a=np.array([.2,.5,.8,.1,.9]);q=DEFAULT_PRIOR
        self.assertAlmostEqual(worst_case_tv_greedy(a,q,0),np.dot(a,q))
        self.assertAlmostEqual(worst_case_tv_greedy(a,q,1),a.min())

if __name__=='__main__': unittest.main()
