"""Transparent 1550-nm atmospheric-only FSO simulation.

Numerical coefficients: Erdogan et al. (2026), IEEE Vehicular Technology
Magazine, Table I/II. Paper: https://doi.org/10.1109/MVT.2026.3687349

Important unit ambiguity: Table I reports dB/km but Eqs. (1)-(3) insert
coefficients directly into exp(-sum coefficient * path). We therefore support
T = exp(-Q) ('paper_exponential') and T = 10**(-Q/10) ('db_label').
Neither interpretation is claimed to be independently physically validated.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product
from math import cos, exp, isclose, isfinite, log, radians, sqrt
import numpy as np

PAPER_EXPONENTIAL = 'paper_exponential'
DB_LABEL = 'db_label'
CONVENTIONS = (PAPER_EXPONENTIAL, DB_LABEL)
WAVELENGTH_NM = 1550
MAX_ZENITH_DEG = 70.0
PROFILES = ('table_ii', 'clear_prose', 'fog_visibility_stress')


@dataclass(frozen=True)
class State:
    name: str
    probability: float
    printed_coefficient_per_km: float

    def __post_init__(self):
        if not (isfinite(self.probability) and 0 <= self.probability <= 1):
            raise ValueError('State probability must be finite and in [0,1]')
        if not (isfinite(self.printed_coefficient_per_km)
                and self.printed_coefficient_per_km >= 0):
            raise ValueError('Coefficient must be nonnegative and finite')


@dataclass(frozen=True)
class Layer:
    name: str
    bottom_km: float
    top_km: float
    states: tuple[State, ...]

    def __post_init__(self):
        if not (isfinite(self.bottom_km) and isfinite(self.top_km)
                and 0 <= self.bottom_km < self.top_km):
            raise ValueError('Layer boundaries must be ordered, finite, nonnegative')
        if not self.states or not isclose(sum(s.probability for s in self.states), 1.0,
                                          rel_tol=0, abs_tol=1e-11):
            raise ValueError('Mutually exclusive layer-state probabilities must sum to 1')


@dataclass(frozen=True)
class Scenario:
    name: str
    layers: tuple[Layer, ...]

    def __post_init__(self):
        if not self.layers or self.layers[0].bottom_km != 0:
            raise ValueError('Scenarios must start at ground level')
        for left, right in zip(self.layers[:-1], self.layers[1:]):
            if not isclose(left.top_km, right.bottom_km, abs_tol=1e-11):
                raise ValueError('Layers must be contiguous without overlaps or gaps')

    @property
    def top_km(self) -> float:
        return self.layers[-1].top_km


def _slab(name: str, lower: float, upper: float,
          *states: tuple[str, float, float]) -> Layer:
    return Layer(name, lower, upper, tuple(State(*x) for x in states))


def scenarios_1550nm(profile: str = "table_ii") -> dict[str, Scenario]:
    """Transcription of Table II, with rainy clear-air 14.2 km split around cloud.

    Table II prints coefficients as dB/km, but Eqs. 1-3 use exp(-coefficient*km).
    The five *conditional* scenarios are not assigned probabilities relative
    to each other. Within a slab, probabilities apply to mutually exclusive states.
    """
    clear = ('clear air', 1.0, 0.0025)
    volcanic = _slab('stratospheric volcanic aerosol', 15, 30,
                     ('high volcanic activity', .5, .0104),
                     ('background volcanic activity', .5, .0002036))
    if profile not in PROFILES:
        raise ValueError('Unknown atmospheric profile')
    scenarios = {
        'rain': Scenario('Rain / nimbostratus', (
            _slab('lower clear air', 0, .6, clear),
            _slab('nimbostratus cloud', .6, 1.4,
                  ('nimbostratus', .9, 8.2425), ('normal air', .1, .034)),
            _slab('upper clear air', 1.4, 15, clear), volcanic)),
        'fog': Scenario('Two-layer fog', (
            _slab('thick fog', 0, 1, ('thick fog', 1, 1.7680)),
            _slab('light fog', 1, 2, ('light fog', 1, .4592)),
            _slab('upper clear air', 2, 15, clear), volcanic)),
        'clear': Scenario('Clear atmosphere', (
            _slab('normal lower air', 0, 3, ('normal air', 1, .034)),
            _slab('upper clear air', 3, 15, clear), volcanic)),
        'pollution': Scenario('Extreme air pollution', (
            _slab('mixed urban aerosol', 0, 3,
                  ('extremely polluted', .7, .3536), ('normal air', .3, .034)),
            _slab('upper clear air', 3, 15, clear), volcanic)),
        'snow': Scenario('Heavy snow', (
            _slab('heavy snow', 0, 2, ('heavy snow', 1, .2)),
            _slab('upper clear air', 2, 15, clear), volcanic)),
    }
    # Preserve the published table; alternative profiles are explicit, not corrections.
    if profile == 'clear_prose':
        scenarios['clear'] = Scenario('Clear atmosphere: Section IV-C prose', (
            _slab('clear air', 0, 15, clear), volcanic))
    elif profile == 'fog_visibility_stress':
        # Al Naboulsi radiation-fog polynomial in native km^-1, converted to dB/km.
        # See doi:10.3390/photonics13111013, Table 1 (1550 nm, V=0.05–1 km).
        # Only fog coefficients change; layer thicknesses remain Table II.
        scenarios['fog'] = Scenario('Radiation-fog coefficient stress case', (
            _slab('thick fog', 0, 1, ('thick fog', 1, radiation_fog_db_per_km(.20))),
            _slab('light fog', 1, 2, ('light fog', 1, radiation_fog_db_per_km(.77))),
            _slab('upper clear air', 2, 15, clear), volcanic))
    return scenarios


def radiation_fog_db_per_km(visibility_km: float, wavelength_um: float = 1.55) -> float:
    """Empirical radiation-fog sensitivity model, not local calibration.

    Wavelength in micrometres, visibility in km, output in dB/km.
    Native extinction and conversion as in doi:10.3390/photonics13111013, Table 1.
    """
    if not (.05 <= visibility_km <= 1 and .69 <= wavelength_um <= 1.55):
        raise ValueError('Outside stated radiation-fog model domain')
    return (10/log(10))*(.18126*wavelength_um**2 + .13709*wavelength_um + 3.7502)/visibility_km


def path_lengths_km(scenario: Scenario, altitude_km: float,
                    zenith_deg: float = 0) -> np.ndarray:
    """Flat, horizontal slab intersection. Zenith = angle from local vertical."""
    if not (isfinite(altitude_km) and 0 <= altitude_km <= scenario.top_km):
        raise ValueError(f'Altitude must be 0 to {scenario.top_km} km')
    if not (isfinite(zenith_deg) and 0 <= zenith_deg <= MAX_ZENITH_DEG):
        raise ValueError(f'Zenith must be 0 to {MAX_ZENITH_DEG} degrees')
    secant = 1.0 / cos(radians(zenith_deg))
    return np.array([max(0., min(altitude_km, l.top_km) - l.bottom_km) * secant
                     for l in scenario.layers], dtype=float)


def integrated_printed_coefficient(scenario: Scenario, altitude_km: float,
                                   zenith_deg: float = 0) -> float:
    """Q = sum(d_j*sum_k(p_jk*c_jk)); dimension depends on interpretation."""
    ds = path_lengths_km(scenario, altitude_km, zenith_deg)
    return float(sum(d*sum(s.probability*s.printed_coefficient_per_km for s in layer.states)
                     for d, layer in zip(ds, scenario.layers)))


def transmittance_from_q(q: float | np.ndarray,
                         convention: str = DB_LABEL):
    """Two explicitly separate readings of the source's coefficient notation."""
    if convention not in CONVENTIONS:
        raise ValueError(f'Unknown convention {convention!r}')
    q = np.asarray(q, dtype=float)
    if np.any(~np.isfinite(q)) or np.any(q < 0):
        raise ValueError('Q must be finite and nonnegative')
    val = np.exp(-q) if convention == PAPER_EXPONENTIAL else np.power(10., -q/10.)
    return float(val) if val.ndim == 0 else val


def loss_db_from_q(q: float | np.ndarray,
                   convention: str = DB_LABEL):
    """Equivalent power loss in dB, *after* choosing a convention."""
    if convention not in CONVENTIONS:
        raise ValueError('Unknown convention')
    return np.asarray(q) * (10. / log(10.) if convention == PAPER_EXPONENTIAL else 1.)


def effective_transmittance(scenario: Scenario, altitude_km: float,
                            zenith_deg: float = 0,
                            convention: str = DB_LABEL) -> float:
    """T_eff = f(E[Q]); *not* generally equal to E[f(Q)]."""
    return transmittance_from_q(integrated_printed_coefficient(
        scenario, altitude_km, zenith_deg), convention)


def exact_distribution(scenario: Scenario, altitude_km: float,
                       zenith_deg: float = 0) -> tuple[np.ndarray, np.ndarray]:
    """Enumerate independent per-layer categorical states (at most 4 here).

    Returns Q values and their probabilities. Independence is an explicit
    teaching assumption, NOT a weather-correlation estimate from ERA5.
    Complexity O(N_layers * product_j K_j); suitable ONLY for few states.
    """
    ds = path_lengths_km(scenario, altitude_km, zenith_deg)
    active = [(l, d) for l, d in zip(scenario.layers, ds) if d > 0]
    if not active:
        return np.array([0.]), np.array([1.])
    q_values, probabilities = [], []
    for selected in product(*(layer.states for layer, _ in active)):
        q_values.append(sum(state.printed_coefficient_per_km*d
                            for state, (_, d) in zip(selected, active)))
        probabilities.append(float(np.prod([s.probability for s in selected])))
    probs = np.asarray(probabilities, dtype=float)
    if not np.isclose(probs.sum(), 1.0, atol=1e-12):
        raise RuntimeError('Enumeration probabilities do not normalize')
    return np.asarray(q_values, dtype=float), probs


def exact_statistics(scenario: Scenario, altitude_km: float,
                     zenith_deg: float = 0, budget_db: float = 3.,
                     convention: str = DB_LABEL) -> dict[str, float]:
    """Exact finite-state E[T] and atmospheric loss-budget exceedance.

    Budget exceedance is NOT receiver outage: receiver, scintillation,
    pointing loss, geometric spread, photodetector noise are absent.
    """
    if not (isfinite(budget_db) and budget_db >= 0):
        raise ValueError('Budget must be finite and nonnegative')
    q, p = exact_distribution(scenario, altitude_km, zenith_deg)
    t = transmittance_from_q(q, convention)
    return {'mean_q': float(np.dot(p, q)),
            'effective_transmittance': effective_transmittance(
                scenario, altitude_km, zenith_deg, convention),
            'mean_transmittance': float(np.dot(p, t)),
            'exceedance_probability': float(np.dot(p, loss_db_from_q(q, convention) > budget_db)),
            'number_of_combinations': len(q)}


def mean_transmittance_factorized(scenario: Scenario, altitude_km: float,
                                  zenith_deg: float = 0,
                                  convention: str = DB_LABEL) -> float:
    """O(sum K_j) analytic E[T] if states in different slabs are independent."""
    ds = path_lengths_km(scenario, altitude_km, zenith_deg)
    product_mean = 1.
    for l, d in zip(scenario.layers, ds):
        product_mean *= sum(s.probability * transmittance_from_q(
            s.printed_coefficient_per_km*d, convention) for s in l.states)
    return float(product_mean)


def sample_q(scenario: Scenario, altitude_km: float, zenith_deg: float = 0,
             n: int = 10000, seed: int = 20261123) -> np.ndarray:
    """Vectorized categorical Monte Carlo (MC), only for cross-checking."""
    if not isinstance(n, (int, np.integer)) or n < 1:
        raise ValueError('Sample count must be positive integer')
    ds = path_lengths_km(scenario, altitude_km, zenith_deg)
    rng = np.random.default_rng(seed)  # PCG64 as currently selected by NumPy default_rng
    total = np.zeros(n, dtype=float)
    for l, d in zip(scenario.layers, ds):
        if d == 0:
            continue
        coeffs = np.array([s.printed_coefficient_per_km for s in l.states])
        probs = np.array([s.probability for s in l.states])
        total += rng.choice(coeffs, size=n, p=probs) * d
    return total


def wilson_interval(successes: int, n: int, z: float = 1.959963984540054):
    """Wilson score interval for Bernoulli trials, approximately 95% for z=1.96."""
    if n < 1 or not 0 <= successes <= n:
        raise ValueError('Invalid count')
    p = successes / n
    denom = 1 + z*z/n
    center = (p + z*z/(2*n))/denom
    half = z * sqrt(p*(1-p)/n + z*z/(4*n*n))/denom
    return max(0., center-half), min(1., center+half)


def uniform_ground_baseline_q(scenario: Scenario, altitude_km: float,
                              zenith_deg: float = 0) -> float:
    """Deliberately naive surface-only baseline; NOT another published model."""
    path_lengths_km(scenario, altitude_km, zenith_deg)
    bottom = scenario.layers[0]
    ground_coefficient = sum(s.probability*s.printed_coefficient_per_km
                             for s in bottom.states)
    return ground_coefficient*altitude_km/cos(radians(zenith_deg))
