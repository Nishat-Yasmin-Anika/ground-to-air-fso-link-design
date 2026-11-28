import math,sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from atmosphere import (PAPER_EXPONENTIAL,DB_LABEL,scenarios_1550nm,
                        exact_distribution,transmittance_from_q)
from fso_link import (Link,DEFAULT_PRIOR,SCENARIO_NAMES,gaussian_aperture_capture,
    capture_via_independent_quadrature,mean_capture_analytic,critical_offset,
    success_probability_for_transmittance,conditional_availability,availability,
    worst_case_tv_greedy,worst_case_tv_lp,min_aperture_for_target,sample_link,
    wilson_score,weather_limited_ceiling,critical_tv_radius)

class PhysicalAndNumericalChecks(unittest.TestCase):
    def setUp(self): self.link=Link(convention=PAPER_EXPONENTIAL)
    def test_01_source_state_probabilities(self):
        for name,s in scenarios_1550nm().items():
            self.assertEqual(s.name,scenarios_1550nm()[name].name)
            for l in s.layers:self.assertAlmostEqual(sum(st.probability for st in l.states),1)
    def test_02_zero_offset_closed_form(self):
        for a,w in [(.1,.2),(.2,.18),(.03,.5)]:
            self.assertAlmostEqual(gaussian_aperture_capture(a,w,0),1-math.exp(-2*a*a/(w*w)),places=11)
    def test_03_independent_bessel_quadrature(self):
        for a,w,r in [(.1,.17,0),(.1,.17,.02),(.1,.17,.13),(.25,.18,.3)]:
            self.assertAlmostEqual(gaussian_aperture_capture(a,w,r),capture_via_independent_quadrature(a,w,r),places=9)
    def test_04_capture_decreases_with_offset(self):
        v=gaussian_aperture_capture(.15,.18,np.linspace(0,.6,100))
        self.assertTrue(np.all(np.diff(v)<=1e-11))
    def test_05_capture_increases_with_aperture(self):
        self.assertLess(gaussian_aperture_capture(.1,.2,.1),gaussian_aperture_capture(.2,.2,.1))
    def test_06_critical_displacement_inversion(self):
        target=.25; r=critical_offset(.12,.18,target)
        self.assertGreater(r,0)
        self.assertAlmostEqual(gaussian_aperture_capture(.12,.18,r),target,places=9)
    def test_07_analytic_mean_capture_convolution(self):
        a,w,s=.14,.2,.065
        mean=mean_capture_analytic(a,w,s)
        rng=np.random.default_rng(2026)
        r=np.hypot(rng.normal(0,s,80000),rng.normal(0,s,80000))
        simulated=np.mean(gaussian_aperture_capture(a,w,r))
        self.assertLess(abs(mean-simulated),.003)
    def test_08_zero_jitter_conditional(self):
        for t in (.001,.5,1):
            ans=success_probability_for_transmittance(t,.15,0,self.link)
            beam=gaussian_aperture_capture(.15,self.link.beam_radius_m,0)
            expected=float(self.link.tx_mw*self.link.optical_efficiency*t*beam>=self.link.threshold_mw)
            self.assertEqual(ans,expected)
    def test_09_independent_rayleigh_pointing_verification(self):
        t=.35;a=.12;j=22
        exact=success_probability_for_transmittance(t,a,j,self.link)
        rng=np.random.default_rng(31);n=100000
        sd=j*1e-6*self.link.length_m
        radial=np.hypot(rng.normal(0,sd,n),rng.normal(0,sd,n))
        mc=(self.link.tx_mw*self.link.optical_efficiency*t*gaussian_aperture_capture(a,self.link.beam_radius_m,radial)>=self.link.threshold_mw).mean()
        self.assertLess(abs(exact-mc),.008)
    def test_10_conditional_probabilities_valid(self):
        v=conditional_availability(.14,15,self.link)
        self.assertEqual(len(v),5)
        self.assertTrue(np.all((v>=0)&(v<=1)))
    def test_11_prior_and_nominal(self):
        v=conditional_availability(.14,15,self.link)
        self.assertAlmostEqual(availability(.14,15,self.link),np.dot(DEFAULT_PRIOR,v),places=10)
    def test_12_robust_exact_lp(self):
        rng=np.random.default_rng(6)
        for _ in range(65):
            p=rng.dirichlet(np.ones(5));v=rng.random(5);rho=float(rng.random())
            self.assertAlmostEqual(worst_case_tv_greedy(v,p,rho),worst_case_tv_lp(v,p,rho),places=8)
    def test_13_robust_is_not_optimistic(self):
        nom=availability(.14,15,self.link)
        self.assertLessEqual(availability(.14,15,self.link,rho=.04),nom)
        self.assertLessEqual(availability(.14,15,self.link,rho=.08),availability(.14,15,self.link,rho=.04))
    def test_14_minimum_aperture_constraint(self):
        r=min_aperture_for_target(.92,15,self.link,rho=.04)
        self.assertTrue(.10<r<.20)
        self.assertAlmostEqual(availability(r,15,self.link,rho=.04),.92,delta=.0003)
        self.assertLess(availability(r-.002,15,self.link,rho=.04),.92)
    def test_15_unachievable_target_flag(self):
        self.assertTrue(math.isnan(min_aperture_for_target(.92,15,self.link,rho=.08)))
    def test_16_stochastic_cross_check(self):
        ex=availability(.14,15,self.link)
        run=sample_link(25000,.14,15,self.link,seed=987)
        self.assertLess(abs(ex-run['availability']),.014)
    def test_17_receiver_power_threshold_monotone(self):
        from dataclasses import replace
        l2=replace(self.link,threshold_mw=self.link.threshold_mw*2)
        self.assertGreaterEqual(availability(.15,15,self.link),availability(.15,15,l2))
    def test_18_different_conventions(self):
        from dataclasses import replace
        l2=replace(self.link,convention=DB_LABEL)
        v1=availability(.09,15,self.link);v2=availability(.09,15,l2)
        self.assertNotAlmostEqual(v1,v2,places=3)
    def test_19_wilson(self):
        lo,hi=wilson_score(5,10)
        self.assertTrue(0<lo<.5<hi<1)
    def test_21_global_availability_ceiling(self):
        c0,s=weather_limited_ceiling(self.link,rho=0)
        self.assertAlmostEqual(c0,.964,places=12)
        self.assertTrue(np.all((s>=0)&(s<=1)))
        self.assertGreaterEqual(c0,availability(.30,15,self.link))
    def test_22_tv_feasibility_threshold(self):
        r=critical_tv_radius(.92,self.link)
        self.assertAlmostEqual(r,(.964-.92)/.9,places=10)
        self.assertLess(weather_limited_ceiling(self.link,rho=.08)[0],.92)
        self.assertGreater(weather_limited_ceiling(self.link,rho=.04)[0],.92)
    def test_23_coefficient_convention_end_to_end_conclusion_changes(self):
        from dataclasses import replace
        a=replace(self.link,convention=DB_LABEL)
        self.assertTrue(math.isinf(critical_tv_radius(.92,a)))
        self.assertAlmostEqual(weather_limited_ceiling(a,rho=.08)[0],1.0)
        self.assertTrue(math.isfinite(min_aperture_for_target(.92,15,a,rho=.08)))
        self.assertTrue(math.isnan(min_aperture_for_target(.92,15,self.link,rho=.08)))
    def test_24_literal_db_implies_less_attenuation_for_positive_coefficients(self):
        import numpy as np
        from atmosphere import transmittance_from_q, PAPER_EXPONENTIAL, DB_LABEL
        q=np.array([0.03,.1,1.,5.,10.])
        self.assertTrue(np.all(transmittance_from_q(q,DB_LABEL)>transmittance_from_q(q,PAPER_EXPONENTIAL)))
    def test_20_weather_probabilities_across_scenarios_not_sourced(self):
        self.assertAlmostEqual(DEFAULT_PRIOR.sum(),1.)
        self.assertEqual(len(SCENARIO_NAMES),len(DEFAULT_PRIOR))

if __name__=='__main__':unittest.main(verbosity=2)
