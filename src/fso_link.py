"""Research-grade *illustrative* ground-to-air FSO link design study.

Model components:
* atmosphere.py transcribes Erdogan et al. (2026) Tables I-II with dual-unit audit
* circular-aperture capture fraction for an offset isotropic 2D Gaussian beam
* independent, zero-mean Gaussian horizontal/vertical pointing-jitter components
* conditional exact optical-power availability (weather mixture, Rayleigh jitter)
* worst-case probability under total-variation (TV) distance <= rho from a nominal
  **illustrative**, not empirically estimated, weather-scenario mixture.

This is not a complete end-to-end communications BER/outage model: atmospheric
scintillation, turbulence fading, pointing temporal dynamics, noise and detector
thermal effects are excluded, and sensitivity is a demonstration threshold.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import math
from typing import Dict
import numpy as np
from scipy.stats import ncx2
from scipy.optimize import brentq, linprog
from scipy.integrate import quad
from scipy.special import i0e
from atmosphere import (PAPER_EXPONENTIAL, DB_LABEL, scenarios_1550nm,
                        exact_distribution, transmittance_from_q, PROFILES)

SCENARIO_NAMES = ('clear','pollution','fog','rain','snow')
# Hypothetical demonstration mixture, NOT ERA5-derived; source paper does
# NOT provide a probability distribution across the five weather scenarios.
DEFAULT_PRIOR = np.array([.76, .10, .07, .04, .03])

@dataclass(frozen=True)
class Link:
    altitude_km: float = 3.0
    zenith_deg: float = 0.0
    tx_mw: float = 50.0
    optical_efficiency: float = 0.70
    threshold_mw: float = 2.0
    beam_waist_m: float = .025
    divergence_urad: float = 55.0
    convention: str = DB_LABEL
    profile: str = "table_ii"

    def __post_init__(self):
        for name in ('altitude_km','tx_mw','optical_efficiency','threshold_mw','beam_waist_m','divergence_urad'):
            x = getattr(self, name)
            if not np.isfinite(x) or x <= 0:
                raise ValueError(f'{name} must be positive and finite')
        if not (0 < self.optical_efficiency <= 1):
            raise ValueError('optical efficiency outside (0,1]')
        if not (0 <= self.zenith_deg <= 70):
            raise ValueError('Zenith out of range')
        if self.convention not in (PAPER_EXPONENTIAL,DB_LABEL):
            raise ValueError('Unknown atmospheric convention')
        if self.profile not in PROFILES:
            raise ValueError('Unknown atmospheric profile')
        if self.profile == 'fog_visibility_stress' and self.convention != DB_LABEL:
            raise ValueError('Radiation-fog model explicitly uses dB/km')
        if self.implied_m_squared < 1 - 1e-12:
            raise ValueError('Waist/divergence imply M² below diffraction limit')
        if self.altitude_km > 30:
            raise ValueError('Source scenarios terminate at 30 km')

    @property
    def length_m(self):
        # Flat Earth and parallel horizontal layers as in atmospheric slab model
        return 1000 * self.altitude_km / math.cos(math.radians(self.zenith_deg))

    @property
    def implied_m_squared(self):
        """Gaussian-equivalent beam quality; not a measured M²."""
        return math.pi*self.beam_waist_m*self.divergence_urad*1e-6/1550e-9

    @property
    def beam_radius_m(self):
        # Simplified far-field Gaussian 1/e^2 intensity radius; **not** a
        # diffraction-limited propagation calculation, beam waist/divergence
        # are independent illustrative inputs.
        return math.hypot(self.beam_waist_m, self.divergence_urad*1e-6*self.length_m)


def gaussian_aperture_capture(a_m: float, w_m: float, displacement_m):
    """Exact integral of 2-D normalized Gaussian intensity over circular aperture.

    I(x,y) = 2/(pi*w^2) exp(-2*||[x,y]-[r,0]||^2/w^2).
    Integrated power = F_{noncentral chi-square(2, lambda)}((2a/w)^2),
    lambda=(2r/w)^2. This is geometrical+pointing collection only.
    """
    if not (math.isfinite(a_m) and math.isfinite(w_m) and a_m > 0 and w_m > 0):
        raise ValueError('Aperture radius and beam radius must be positive')
    r = np.asarray(displacement_m)
    if np.any(~np.isfinite(r)) or np.any(r < 0):
        raise ValueError('Displacement must be >=0')
    x = (2*a_m/w_m)**2
    return ncx2.cdf(x, df=2, nc=(2*r/w_m)**2)


def capture_via_independent_quadrature(a: float,w: float,r: float) -> float:
    """Independent radial integration using scaled modified Bessel I_0.

    4s/w^2 * exp(-2*(s-r)^2/w^2) * i0e(4sr/w^2).
    """
    if not all(math.isfinite(v) for v in (a,w,r)) or a <= 0 or w <= 0 or r < 0:
        raise ValueError('Invalid aperture geometry')
    def f(s):
        z = 4*s*r/(w*w)
        return 4*s/(w*w) * math.exp(-2*(s-r)**2/(w*w)) * i0e(z)
    return quad(f,0,a,epsabs=1e-11,epsrel=1e-10)[0]


def mean_capture_analytic(a: float,w: float,sigma_m: float):
    """Exact E[g(R)] for zero-mean 2D Gaussian jitter with axis SD sigma_m.

    Follows by convolution of independent 2D Gaussian photon location
    N(0,w^2/4 I) and pointing offset N(0,sigma^2 I).
    """
    if not all(math.isfinite(v) for v in (a,w,sigma_m)) or a <= 0 or w <= 0 or sigma_m < 0:
        raise ValueError('Invalid aperture geometry or jitter')
    return -math.expm1(-a*a/(2*(sigma_m*sigma_m+w*w/4)))


def critical_offset(a: float,w: float,required_capture: float) -> float:
    """Find largest radial displacement allowing capture >= required_capture.

    Monotonicity is valid for a centered circular receiver and a radially
    symmetric Gaussian beam (no boresight offset). Returns 0 if impossible.
    """
    if not all(math.isfinite(v) for v in (a,w,required_capture)) or a <= 0 or w <= 0:
        raise ValueError("Invalid aperture or required capture")
    if required_capture <= 0: return math.inf
    g0 = -math.expm1(-2*a*a/(w*w))
    if required_capture >= g0: return 0.0
    # Gaussian tail bound: if r>a, capture <= exp[-2(r-a)^2/w²].
    hi = a + w*math.sqrt(-math.log(required_capture)/2) + w
    if not math.isfinite(hi): raise ValueError('Geometry exceeds numeric range')
    return brentq(lambda r: gaussian_aperture_capture(a,w,r)-required_capture,
                  0,hi, xtol=1e-12, rtol=1e-11)


def success_probability_for_transmittance(t: float,a: float,jitter_urad:float,link:Link) -> float:
    """Exact P(P_rx >= P_threshold) conditioned on atmospheric state.

    Jitter is independent zero-mean Gaussian in x/y (Rayleigh magnitude).
    """
    if not math.isfinite(jitter_urad) or jitter_urad < 0: raise ValueError('Invalid jitter')
    if not math.isfinite(a) or a <= 0: raise ValueError('Invalid aperture')
    if not math.isfinite(t) or not 0 <= t <= 1: raise ValueError('Invalid transmittance')
    if t == 0: return 0.0
    needed = link.threshold_mw/(link.tx_mw*link.optical_efficiency*t)
    if needed >= 1: return 0.0
    rcrit = critical_offset(a,link.beam_radius_m,needed)
    if math.isinf(rcrit): return 1.
    if jitter_urad == 0:
        return float(needed <= -math.expm1(-2*a*a/link.beam_radius_m**2))
    sigma_m = jitter_urad*1e-6*link.length_m
    return -math.expm1(-0.5*(rcrit/sigma_m)**2)


def conditional_availability(a:float,jitter_urad:float,link:Link) -> np.ndarray:
    """Exact within-scenario categorical-state mixture + Rayleigh jitter CDF."""
    if a <= 0: raise ValueError('a must be positive')
    values=[]
    for name in SCENARIO_NAMES:
        q,prob=exact_distribution(scenarios_1550nm(link.profile)[name],link.altitude_km,link.zenith_deg)
        trans=transmittance_from_q(q,link.convention)
        chance=[success_probability_for_transmittance(float(t),a,jitter_urad,link) for t in trans]
        values.append(float(np.clip(np.dot(prob,chance),0,1)))
    return np.array(values)


def validate_prior(q):
    q=np.asarray(q,dtype=float)
    if q.shape != (len(SCENARIO_NAMES),) or np.any(q<0) or not np.all(np.isfinite(q)) or abs(q.sum()-1)>1e-10:
        raise ValueError('Prior must be 5 nonnegative normalized probabilities')
    return q


def worst_case_tv_greedy(chances, prior, rho:float) -> float:
    """Minimize p·chances for p in simplex and total-variation(p,prior)<=rho.

    For linear objectives, transfer probability mass from high-reward states
    to low-reward states until the TV budget is used. Complexity O(S log S).
    """
    p=validate_prior(prior).copy()
    a=np.asarray(chances,dtype=float)
    if a.shape!=p.shape or np.any(~np.isfinite(a)) or np.any(a<0) or np.any(a>1):
        raise ValueError('Invalid availability vector')
    if not 0<=rho<=1: raise ValueError('TV radius must be in [0,1]')
    ranks=np.argsort(a)
    lo, hi=0,len(a)-1
    budget=rho
    while lo<hi and budget>1e-14:
        donor=int(ranks[hi]); recipient=int(ranks[lo])
        if a[donor]-a[recipient]<=1e-13: break
        mass=min(budget,p[donor],1-p[recipient])
        if mass <= 1e-14:
            if p[donor]<=1e-14: hi-=1
            if 1-p[recipient]<=1e-14: lo+=1
            continue
        p[donor]-=mass; p[recipient]+=mass; budget-=mass
        if p[donor]<=1e-14: hi-=1
        if 1-p[recipient]<=1e-14: lo+=1
    return float(np.clip(np.dot(p,a),0,1))


def worst_case_tv_lp(chances, prior, rho:float):
    """Independent linear-programming reference for the greedy TV solver."""
    p0=validate_prior(prior)
    a=np.asarray(chances,dtype=float)
    if a.shape!=p0.shape or np.any(~np.isfinite(a)) or np.any(a<0) or np.any(a>1) or not 0<=rho<=1:
        raise ValueError('Invalid LP inputs')
    n=len(p0)
    cost=np.r_[a,np.zeros(n)]
    A=[]; b=[]
    for i in range(n):
        row=np.zeros(2*n);row[i]=1;row[n+i]=-1; A.append(row);b.append(p0[i])
        row=np.zeros(2*n);row[i]=-1;row[n+i]=-1; A.append(row);b.append(-p0[i])
    row=np.r_[np.zeros(n),np.ones(n)];A.append(row);b.append(2*rho)
    eq=np.r_[np.ones(n),np.zeros(n)][None,:]
    solution=linprog(cost,A_ub=np.asarray(A),b_ub=np.asarray(b),A_eq=eq,b_eq=[1],bounds=[(0,None)]*(2*n),method='highs')
    if not solution.success: raise RuntimeError(solution.message)
    return float(solution.fun)


def availability(a,jitter_urad,link,prior=DEFAULT_PRIOR,rho=0.):
    vec=conditional_availability(a,jitter_urad,link)
    if rho==0: return float(np.clip(np.dot(validate_prior(prior),vec),0,1))
    return worst_case_tv_greedy(vec,prior,rho)


def min_aperture_for_target(target,jitter_urad,link,prior=DEFAULT_PRIOR,rho=0.,a_lo=.025,a_hi=.50,atol=1e-7):
    """Return the feasible endpoint of a monotone search, within [a_lo,a_hi].

    NaN means no feasible aperture in the search interval; consult the
    atmosphere-only ceiling separately. Handles discontinuous zero-jitter steps.
    """
    if not (0 < target < 1): raise ValueError('Invalid target')
    if not all(math.isfinite(v) for v in (a_lo,a_hi,atol)) or not 0<a_lo<=a_hi or atol<=0:
        raise ValueError('Invalid aperture interval or tolerance')
    f=lambda a: availability(a,jitter_urad,link,prior,rho)
    if f(a_hi)<target: return math.nan
    if f(a_lo)>=target: return a_lo
    lo,hi=a_lo,a_hi
    while hi-lo>atol:
        mid=(lo+hi)/2
        if mid==lo or mid==hi: break
        if f(mid)>=target: hi=mid
        else: lo=mid
    return hi


def sample_link(n:int,a:float,jitter_urad:float,link:Link,prior=DEFAULT_PRIOR,seed=20261123):
    """Independent Monte Carlo: draw weather scenario, then its slab states,
    then 2D pointing offsets; evaluate physical collection CDF directly.
    Does NOT sample Bernoulli successes from analytic availability.
    """
    if not isinstance(n,(int,np.integer)) or n<2: raise ValueError('Need at least two draws')
    if not math.isfinite(a) or a<=0 or not math.isfinite(jitter_urad) or jitter_urad<0:
        raise ValueError('Invalid aperture or jitter')
    prior=validate_prior(prior)
    rng=np.random.default_rng(seed)
    which=rng.choice(len(SCENARIO_NAMES),size=n,p=prior)
    q_all=np.empty(n)
    # Use explicit per-layer independently drawn states, not exact enumerated
    # results, to provide an independent stochastic implementation.
    for idx,name in enumerate(SCENARIO_NAMES):
        mask=which==idx; k=int(mask.sum())
        if not k:continue
        scenario=scenarios_1550nm(link.profile)[name]
        qv=np.zeros(k)
        for slab in scenario.layers:
            d=max(0.,min(link.altitude_km,slab.top_km)-slab.bottom_km)/math.cos(math.radians(link.zenith_deg))
            if d==0: continue
            coeff=np.array([s.printed_coefficient_per_km for s in slab.states])
            prob=np.array([s.probability for s in slab.states])
            qv += d*rng.choice(coeff,size=k,p=prob)
        q_all[mask]=qv
    t=transmittance_from_q(q_all,link.convention)
    sigma=jitter_urad*1e-6*link.length_m
    x=rng.normal(0,sigma,n);y=rng.normal(0,sigma,n)
    capture=gaussian_aperture_capture(a,link.beam_radius_m,np.hypot(x,y))
    power=link.tx_mw*link.optical_efficiency*t*capture
    passed=(power>=link.threshold_mw) & (link.tx_mw*link.optical_efficiency*t>link.threshold_mw)
    return {'n':int(n),'success_count':int(passed.sum()),'availability':float(passed.mean()),
            'mean_received_mw':float(power.mean()),'std_received_mw':float(power.std(ddof=1))}


def wilson_score(count:int,n:int,z=1.959963984540054):
    if n<1 or count<0 or count>n:raise ValueError('Invalid count')
    phat=count/n; denom=1+z*z/n
    center=(phat+z*z/(2*n))/denom
    delta=z/denom*math.sqrt(phat*(1-phat)/n+z*z/(4*n*n))
    return max(0.,center-delta),min(1.,center+delta)


def weather_limited_ceiling(link:Link, prior=DEFAULT_PRIOR, rho=0.):
    """Upper bound on availability for ANY finite aperture and jitter.

    In the a -> infinity limit capture -> 1 for each finite offset, so only
    states with P_tx*eta*T > power threshold can ever pass at finite radius. Hence this
    is a global model-feasibility certificate, not merely grid infeasibility.
    """
    limits=[]
    for name in SCENARIO_NAMES:
        q,p=exact_distribution(scenarios_1550nm(link.profile)[name],link.altitude_km,link.zenith_deg)
        t=transmittance_from_q(q,link.convention)
        limits.append(float(np.dot(p,link.tx_mw*link.optical_efficiency*t>link.threshold_mw)))
    conditional=np.array(limits)
    cap=(float(np.dot(validate_prior(prior),conditional)) if rho==0 else
         worst_case_tv_greedy(conditional,prior,rho))
    return cap,conditional


def critical_tv_radius(target:float,link:Link,prior=DEFAULT_PRIOR):
    """Boundary TV radius where the ceiling reaches target (strict failure beyond).

    This is the exact theoretical break-even radius for the model's weather
    frequency ambiguity, found with a one-dimensional monotone bisection.
    """
    if not 0 < target < 1:raise ValueError('Invalid target')
    f=lambda rho:weather_limited_ceiling(link,prior,rho)[0]-target
    if f(0)<0:return 0.
    if f(1)>=0:return math.inf
    return brentq(f,0,1,xtol=1e-12)
