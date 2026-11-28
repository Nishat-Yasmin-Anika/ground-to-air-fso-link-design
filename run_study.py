"""Generate fully reproducible results; launch: python run_study.py.

All generated artifacts go under results/; no figure is hand-edited.
"""
import os,sys,json,csv,math,time,platform,hashlib, subprocess
from pathlib import Path
import numpy as np
import scipy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from dataclasses import asdict, replace
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from atmosphere import (PAPER_EXPONENTIAL,DB_LABEL,scenarios_1550nm,exact_distribution,
                        transmittance_from_q, radiation_fog_db_per_km, effective_transmittance, path_lengths_km)
from fso_link import (Link,SCENARIO_NAMES,DEFAULT_PRIOR,gaussian_aperture_capture,
    capture_via_independent_quadrature,mean_capture_analytic,conditional_availability,
    availability,worst_case_tv_greedy,worst_case_tv_lp,min_aperture_for_target,
    sample_link,wilson_score,weather_limited_ceiling,critical_tv_radius, success_probability_for_transmittance)

OUT=ROOT/'results'; FIG=OUT/'figures'; TBL=OUT/'tables'; META=OUT/'metadata'
for d in (FIG,TBL,META):d.mkdir(parents=True,exist_ok=True)
link=Link()  # literal dB/km by default
SEED=20261123
TARGET=.92
RHO=.04
FAST=os.environ.get('FAST_MODE','1') != '0'
N_MC=20000 if FAST else 100000
DPI=165
plt.rcParams.update({'figure.dpi':125,'savefig.dpi':DPI,'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
start=time.perf_counter()

def savefig(name):
    plt.tight_layout();plt.savefig(FIG/(name+'.png'));plt.savefig(FIG/(name+'.svg'));plt.close()

def csvout(name, header, rows):
    with (TBL/name).open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f);writer.writerow(header)
        for row in rows:writer.writerow(row)

# 01: model verification + Gaussian collection geometry
aperture=.14
r=np.linspace(0,.42,140)
w=link.beam_radius_m
g=gaussian_aperture_capture(aperture,w,r)
ind_offsets=[0,.05,.1,.16,.25]
ind_check=np.array([capture_via_independent_quadrature(aperture,w,x) for x in ind_offsets])
assert np.allclose(ind_check,gaussian_aperture_capture(aperture,w,ind_offsets),atol=1e-10)
plt.figure(figsize=(7,4.3))
plt.plot(r,g,label='Noncentral chi-square CDF (exact)')
plt.scatter(ind_offsets,ind_check,label='Independent Bessel quadrature',marker='o',s=24,zorder=3)
plt.xlabel('Beam-centre displacement at receiver (m)')
plt.ylabel('Captured optical-power fraction')
plt.title('01 | Finite circular aperture: exact Gaussian-beam overlap')
plt.ylim(-.03,1.03);plt.legend(loc='upper right',fontsize=8)
savefig('01_aperture_integral_validation')

# 02: source coefficient convention and different weather paths
rows=[]
for name in SCENARIO_NAMES:
    q,pr=exact_distribution(scenarios_1550nm()[name],link.altitude_km,link.zenith_deg)
    for convention in [PAPER_EXPONENTIAL,DB_LABEL]:
        t=transmittance_from_q(q,convention)
        rows.append((name,convention,float(np.dot(pr,t)),float(np.min(t)),float(np.max(t)),len(q)))
csvout('01_weather_scenarios_and_conventions.csv',['scenario','convention','mean_transmittance','minimum_transmittance','maximum_transmittance','finite_states'],rows)
plt.figure(figsize=(8.4,4.6));idx=np.arange(len(SCENARIO_NAMES))
y_a=np.array([r[2] for r in rows[::2]])
y_b=np.array([r[2] for r in rows[1::2]])
plt.bar(idx-.19,y_a,width=.38,label='Equation-as-printed: exp(-Q)')
plt.bar(idx+.19,y_b,width=.38,label='Unit-label interpretation: 10^(-Q/10)')
plt.xticks(idx,SCENARIO_NAMES)
plt.ylabel('Mean atmospheric transmittance (unitless)')
plt.title('02 | 3-km atmosphere: published coefficient-notation ambiguity')
plt.legend(fontsize=8);savefig('02_atmospheric_unit_interpretations')

# 03: availability vs receiver aperture, at three pointing-jitter levels
radii=np.linspace(.025,.30,56)
calculated={}
plt.figure(figsize=(8.6,5.1))
for jitter in [8,15,25]:
    nominal=np.array([availability(a,jitter,link) for a in radii]);robust=np.array([availability(a,jitter,link,rho=RHO) for a in radii])
    calculated[jitter]=(nominal,robust)
    plt.plot(radii*200,nominal,label=f'Nominal, jitter {jitter} µrad')
    plt.plot(radii*200,robust,linestyle='--',label=f'TV-robust, jitter {jitter} µrad')
plt.axhline(TARGET,color='black',ls=':',label='Target availability: 92%')
plt.xlabel('Receiver aperture diameter (cm)');plt.ylabel('Optical-power availability')
plt.title('03 | Nominal versus uncertain-weather design')
plt.ylim(0,1.00);plt.legend(loc='lower right',ncol=2,fontsize=7)
savefig('03_availability_vs_aperture')

# 04: design frontier
frontier=[]
for jitter in [5,8,10,12,15,18,20,22,25,28,30]:
    for rho in [0,RHO,.08]:
        a=min_aperture_for_target(TARGET,jitter,link,rho=rho)
        frontier.append((jitter,rho, float(2*a*100) if np.isfinite(a) else None,
                         'feasible' if np.isfinite(a) else 'infeasible within 1.0m diameter'))
csvout('02_minimum_aperture_frontier.csv',['jitter_sigma_per_axis_urad','TV_radius','minimum_aperture_diameter_cm','status'],frontier)
plt.figure(figsize=(7.8,4.7))
for rho,style in [(0,'-'),(RHO,'--')]:
    v=[r for r in frontier if abs(r[1]-rho)<1e-9]
    y=np.array([np.nan if x[2] is None else x[2] for x in v])
    plt.plot([x[0] for x in v],y,linestyle=style,marker='o',label=f'TV radius {rho:.0%}')
plt.xlabel('Pointing angular jitter: per-axis SD (µrad)')
plt.ylabel('Minimum receiver aperture diameter (cm)')
plt.title('04 | Design trade-off: jitter control versus aperture')
v=[r for r in frontier if abs(r[1]-.08)<1e-9]
plt.plot([x[0] for x in v],[np.nan if x[2] is None else x[2] for x in v],linestyle=':',marker='o',label='TV radius 8%')
plt.legend(fontsize=9);savefig('04_minimum_aperture_frontier')

# 05: uncertainty sensitivity at fixed hardware, includes exact LP reference
jitter=15; ap=.08
vec=conditional_availability(ap,jitter,link)
rad=np.linspace(0,.16,35)
values=np.array([worst_case_tv_greedy(vec,DEFAULT_PRIOR,float(z)) for z in rad])
lp_points=[0,.02,.04,.08,.12,.16];lp_res=[worst_case_tv_lp(vec,DEFAULT_PRIOR,z) for z in lp_points]
assert np.allclose(lp_res,[worst_case_tv_greedy(vec,DEFAULT_PRIOR,z) for z in lp_points],atol=1e-9)
plt.figure(figsize=(7.7,4.6))
plt.plot(rad,values,label='Exact TV worst-case mass transfer')
plt.scatter(lp_points,lp_res,color='black',s=20,label='Independent linear program')
plt.axhline(TARGET,ls=':',color='grey',label='92% target')
plt.xlabel('TV radius: maximum probability mass reassigned')
plt.ylabel('Worst-case optical-power availability')
plt.title('05 | Sensitivity to uncertain weather frequencies')
plt.ylim(max(0,min(values)-.03),1);plt.legend(fontsize=8);savefig('05_weather_probability_shift')
csvout('03_tv_radius_sensitivity.csv',['TV_radius','worst_case_availability'],zip(rad,values))

# 06: feasibility heat map across TV radius and aperture
rho_grid=np.linspace(0,.10,24)
ap_grid=np.linspace(.025,.20,35)
mat=np.array([[availability(a,15,link,rho=rr) for a in ap_grid] for rr in rho_grid])
fig,ax=plt.subplots(figsize=(8.1,5.0))
im=ax.pcolormesh(ap_grid*200,rho_grid,mat,shading='nearest',cmap='viridis',vmin=float(mat.min()),vmax=1.)
fig.colorbar(im,ax=ax,label='Worst-case optical-power availability')
try: ax.contour(ap_grid*200,rho_grid,mat,levels=[TARGET],colors='white',linewidths=1.6)
except ValueError: pass
ax.set_xlabel('Receiver aperture diameter (cm)');ax.set_ylabel('TV radius')
ax.set_title('06 | Feasible region: robust availability threshold at 15 µrad jitter')
savefig('06_design_feasibility_map')

# 07: ablation of weather/jitter vs combined; no false claim of outage BER
ablation=[]
for a in radii:
    joint=availability(a,15,link)
    weather_only=availability(a,0,link)
    # No atmospheric extinction; stochastic pointing jitter retained.
point_only = success_probability_for_transmittance(1., a, 15, link)
    ideal=success_probability_for_transmittance(1.,a,0,link)
    ablation.append((a,joint,weather_only,point_only,ideal))
csvout('04_ablation.csv',['aperture_radius_m','joint_weather_and_pointing','weather_only_zero_jitter','no_extinction_pointing_only','no_extinction_no_jitter'],ablation)
plt.figure(figsize=(8,4.7))
for ii,label in [(1,'Joint: weather + pointing'),(2,'Weather mixture; no jitter'),(3,'No extinction; jitter'),(4,'No extinction; no jitter')]:
    plt.plot(radii*200,[row[ii] for row in ablation],label=label)
plt.axhline(TARGET,ls=':',color='grey')
plt.xlabel('Receiver aperture diameter (cm)');plt.ylabel('Nominal optical-power availability')
plt.title('07 | Ablation: weather state and pointing both matter')
plt.ylim(-.01,1.01);plt.legend(fontsize=8);savefig('07_ablation')

# 08: independent Monte Carlo vs exact model and Wilson CIs
N_levels=[1000,5000,N_MC]
exact=availability(ap,15,link)
mc_rows=[]
for n in N_levels:
    st=time.perf_counter(); result=sample_link(n,ap,15,link,seed=SEED+n)
    elapsed=time.perf_counter()-st
    low,high=wilson_score(result['success_count'],n)
    mc_rows.append((n,result['success_count'],result['availability'],low,high,exact,
                    result['mean_received_mw'],elapsed))
csvout('05_monte_carlo_verification.csv',['samples','successes','sample_availability','Wilson95_lower','Wilson95_upper','exact_availability','sample_mean_power_mw','elapsed_seconds'],mc_rows)
plt.figure(figsize=(7.8,4.4))
for n,k,hat,lo,hi,an,mw,dt in mc_rows:
    plt.errorbar([n],[hat],yerr=[[hat-lo],[hi-hat]],fmt='o',capsize=5)
plt.axhline(exact,color='black',ls='--',label=f'Exact: {exact:.4f}')
plt.xscale('log');plt.xlabel('Monte Carlo samples (log scale)')
plt.ylabel('Optical-power availability');plt.title('08 | Independent Monte Carlo versus exact probability')
plt.legend();savefig('08_monte_carlo_validation')

# 06 extra: illustrative alternative priors (total sum=1 each, not measured)
alt_priors={'baseline_illustrative':DEFAULT_PRIOR,
            'more_fog':np.array([.68,.10,.15,.04,.03]),
            'more_rain':np.array([.72,.10,.07,.08,.03]),
            'favorable_clear':np.array([.84,.06,.04,.04,.02])}
prior_rows=[]
for label, prior in alt_priors.items():
    for rho in [0,.04]:
        prob=availability(.14,15,link,prior,rho)
        needed=min_aperture_for_target(TARGET,15,link,prior,rho)
        prior_rows.append((label,*[round(float(v),5) for v in prior],rho,prob,float(needed) if np.isfinite(needed) else None))
csvout('06_alternate_illustrative_weather_priors.csv',
       ['prior_label',*[f'p_{x}' for x in SCENARIO_NAMES],'TV_radius','availability_at_radius_14cm','minimum_radius_m_target_92pct'],prior_rows)

# 09: legacy atmospheric ceiling / global feasibility certificate
# Retain this plot for reproducibility of the earlier exponential case only.
legacy=replace(link,convention=PAPER_EXPONENTIAL)
rho_l=np.linspace(0,.11,90)
caps=np.array([weather_limited_ceiling(legacy,rho=float(z))[0] for z in rho_l])
critical=critical_tv_radius(TARGET,legacy)
rows=[(float(r),float(v),int(v>=TARGET)) for r,v in zip(rho_l,caps)]
csvout('07_atmospheric_feasibility_ceiling.csv',
       ['TV_radius','global_atmosphere_limited_availability_ceiling','target_92pct_not_excluded'],rows)
plt.figure(figsize=(8,4.7))
plt.plot(rho_l,caps,label='Maximum possible modeled availability (infinite aperture)')
plt.axhline(TARGET,color='black',ls=':',label='Target 92%')
plt.axvline(critical,color='darkred',ls='--',label=f'Break-even TV radius {critical:.4f}')
plt.fill_between(rho_l,caps,TARGET,where=(caps<TARGET),color='red',alpha=.12,label='Globally infeasible region')
plt.xlabel('Weather-probability total-variation radius')
plt.ylabel('Maximum availability permitted by atmospheric transmission')
plt.ylim(.82,1.0)
plt.title('09 | Legacy exponential convention: atmospheric ceiling')
plt.legend(loc='lower left',fontsize=8)
savefig('09_atmospheric_feasibility_ceiling')


# 10: Mandatory end-to-end convention sensitivity of the optimization itself.
# The published coefficient table says dB/km while the equation uses exp(-Q).
# Main physics/design conclusions must be conditional on this unresolved choice.
convention_rows=[]
for conv in (PAPER_EXPONENTIAL,DB_LABEL):
    c_link=replace(link,convention=conv)
    for rho in (0., .04, .08):
        radius=min_aperture_for_target(TARGET,15,c_link,rho=rho)
        ceiling,_=weather_limited_ceiling(c_link,rho=rho)
        convention_rows.append((conv,rho,200*radius if np.isfinite(radius) else None,
            float(ceiling),bool(ceiling + 1e-10 < TARGET)))
csvout('08_optimization_convention_sensitivity.csv',
       ['coefficient_convention','TV_radius','minimum_aperture_diameter_cm_at_15urad',
        'atmosphere_only_availability_ceiling','globally_infeasible'],convention_rows)
fig,ax=plt.subplots(1,2,figsize=(11.0,4.5))
for c,marker in ((PAPER_EXPONENTIAL,'o'),(DB_LABEL,'s')):
    ss=[x for x in convention_rows if x[0]==c]
    radii=[float('nan') if x[2] is None else x[2] for x in ss]
    ax[0].plot([x[1]*100 for x in ss],radii,marker=marker,label=('Equation as printed: exp(-Q)' if c==PAPER_EXPONENTIAL else 'Literal label: 10^(-Q/10)'))
    ax[1].plot([x[1]*100 for x in ss],[x[3] for x in ss],marker=marker,label=('Equation as printed' if c==PAPER_EXPONENTIAL else 'Literal dB/km'))
ax[0].set(xlabel='TV probability shift (%)',ylabel='Minimum aperture diameter (cm)',title='Required aperture for a 92% target')
ax[1].set(xlabel='TV probability shift (%)',ylabel='Atmosphere-only maximum availability',title='Model feasibility bound')
ax[1].axhline(TARGET,color='black',ls=':',label='92% target')
for a in ax: a.grid(alpha=.2);a.legend(fontsize=7)
fig.suptitle('10 | Main engineering conclusions depend on the coefficient convention',fontsize=11)
savefig('10_optimization_convention_sensitivity')

# 11: independent model stress cases and several availability targets.
profiles=[('table_ii_db',link),('table_ii_legacy',legacy),
          ('clear_prose_db',replace(link,profile='clear_prose')),
          ('fog_visibility_db',replace(link,profile='fog_visibility_stress'))]
model_rows=[]
for name,cl in profiles:
    for target in [.90,.92,.95,.99,.999]:
        for rho in [0.,.04,.08]:
            ceiling,_=weather_limited_ceiling(cl,rho=rho)
            a=min_aperture_for_target(target,15,cl,rho=rho)
            status=('feasible_in_interval' if np.isfinite(a) else
                    'ceiling_excludes_target' if ceiling<target else 'not_feasible_in_interval')
            achieved=availability(a,15,cl,rho=rho) if np.isfinite(a) else None
            model_rows.append((name,target,rho,200*a if np.isfinite(a) else None,ceiling,achieved,status))
            if np.isfinite(a): assert achieved>=target
csvout('09_model_and_target_sensitivity.csv',['profile','target','tv_radius','diameter_cm','finite_aperture_ceiling','achieved_availability','status'],model_rows)
fig,ax=plt.subplots(1,2,figsize=(10,4.5))
for name,cl in profiles:
    rs=[r for r in model_rows if r[0]==name and r[1]==.92]
    ax[0].plot([r[2]*100 for r in rs],[np.nan if r[3] is None else r[3] for r in rs],marker='o',label=name)
    ax[1].plot([r[2]*100 for r in rs],[r[4] for r in rs],marker='o',label=name)
ax[0].set(xlabel='TV radius (%)',ylabel='Minimum diameter (cm)',title='92% target: model sensitivity')
ax[1].set(xlabel='TV radius (%)',ylabel='Atmospheric upper bound',title='Feasibility bound')
ax[1].axhline(.92,color='black',ls=':')
for a in ax:a.legend(fontsize=7);a.grid(alpha=.2)
savefig('11_model_and_target_sensitivity')

# 12: comparison against a separate published radiation-fog model, not measurement.
vis=np.array([.05,.20,.50,.77])
published=np.array([7.0721,1.7680,.7072,.4592])
external=np.array([radiation_fog_db_per_km(v) for v in vis])
csvout('10_fog_model_benchmark.csv',['visibility_km','table_I_label_db_per_km','legacy_effective_db_per_km','radiation_fog_native_extinction_per_km','radiation_fog_converted_db_per_km'],zip(vis,published,published*10/np.log(10),external*np.log(10)/10,external))
plt.figure(figsize=(7,4.5));plt.loglog(vis,published,'o-',label='Table I literal dB/km');plt.loglog(vis,published*10/np.log(10),'s--',label='Legacy exponential equivalent dB/km');plt.loglog(vis,external,'^-',label='Radiation fog: converted dB/km');plt.loglog(vis,external*np.log(10)/10,'x:',label='Radiation polynomial as dB (diagnostic)')
plt.xlabel('Visibility (km)');plt.ylabel('Specific attenuation (dB/km)');plt.title('12 | Fog model discrepancy (not measurement validation)');plt.legend(fontsize=8);plt.grid(alpha=.2);savefig('12_fog_model_benchmark')

# 13: multi-geometry, multi-seed numerical verification, with analytic mean-power check.
mc_multi=[]
for name,cl in [('db_vertical',link),('legacy_vertical',legacy),('db_slant',replace(link,altitude_km=2.,zenith_deg=30.)),('fog_stress',replace(link,profile='fog_visibility_stress'))]:
    a=.08; j=15.; ex=availability(a,j,cl)
    tmean=sum(p*float(np.dot(pr,transmittance_from_q(q,cl.convention))) for p,scenario in zip(DEFAULT_PRIOR,SCENARIO_NAMES) for q,pr in [exact_distribution(scenarios_1550nm(cl.profile)[scenario],cl.altitude_km,cl.zenith_deg)])
    mean=cl.tx_mw*cl.optical_efficiency*tmean*mean_capture_analytic(a,cl.beam_radius_m,j*1e-6*cl.length_m)
    for seed in [SEED+11,SEED+22,SEED+33]:
        n=20000 if FAST else 100000
        out=sample_link(n,a,j,cl,seed=seed); lo,hi=wilson_score(out['success_count'],n)
        err=abs(out['availability']-ex); se=math.sqrt(ex*(1-ex)/n)
        power_se=out['std_received_mw']/math.sqrt(n)
        # Conservative simultaneous diagnostic tolerance; not a field-validation claim.
        assert err<=5*se+5/n
        assert abs(out['mean_received_mw']-mean)<=5*power_se+1e-9
        mc_multi.append((name,seed,n,ex,out['availability'],lo,hi,mean,out['mean_received_mw'],power_se,err))
csvout('11_multi_case_mc.csv',['case','seed','n','analytic_availability','mc_availability','wilson95_lower','wilson95_upper','analytic_mean_mw','mc_mean_mw','mc_mean_standard_error_mw','absolute_availability_error'],mc_multi)

# Runtime and reproducibility information
config={
    'paper_source':'https://doi.org/10.1109/MVT.2026.3687349',
    'arxiv_manuscript':'https://arxiv.org/abs/2604.18207',
    'paper_table_II_finite_states':True,
    'weather_scenario_priors_empirically_estimated':False,
    'weather_prior_order':list(SCENARIO_NAMES),
    'weather_prior_values':DEFAULT_PRIOR.tolist(),
    'reference_link':asdict(link),
    'target_availability':TARGET,
    'tv_radius':RHO,
    'monte_carlo_seed_base':SEED,
    'fast_mode':FAST,
    'monte_carlo_samples_max':N_MC,
    'method':'exact conditional mixture + Rayleigh jitter CDF + TV mass transfer; independent scipy linprog and random draws',
    'receiver_power_threshold_is_illustrative_not_device_data':True,
    'propagation_convention_primary':DB_LABEL,
    'legacy_convention_is_source_comparison_only':True,
    'implied_gaussian_equivalent_m_squared':link.implied_m_squared,
    'minimum_aperture_search_radius_m':[.025,.50],
    'source_profiles':[name for name,_ in profiles],
    'end_to_end_sensitivity_in_both_conventions':True,
    'note':'Only single-link optical-power availability; not BER or field reliability.'
}
(META/'run_config.json').write_text(json.dumps(config,indent=2),encoding='utf8')
(META/'environment.json').write_text(json.dumps({'python':sys.version.split()[0],
    'numpy':np.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__,
    'platform':platform.platform(),'os_cpu_count':os.cpu_count()},indent=2),encoding='utf8')
# Explicit timing measures end-to-end including plotting and storage, not estimated Colab
run_secs=time.perf_counter()-start
(META/'runtime.json').write_text(json.dumps({'wall_seconds_end_to_end_approx':run_secs,
'host':'machine on which this script was executed (see environment.json)','fast_mode':FAST,'mc_max_samples':N_MC,
'peak_process_rss_mib_linux':(__import__('resource').getrusage(__import__('resource').RUSAGE_SELF).ru_maxrss/1024 if sys.platform.startswith('linux') else None)},indent=2),encoding='utf8')
paths=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='manifest.json' and not p.name.startswith('.'))
manifest={'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'src/atmosphere.py',ROOT/'src/fso_link.py',ROOT/'run_study.py',ROOT/'tests/test_link.py',ROOT/'tests/test_audit.py'] if p.exists()},'files':[{'path':str(p.relative_to(OUT)), 'bytes':p.stat().st_size,
    'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]}
(META/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
print('RESULTS_READY',len(list(FIG.glob('*.png'))),'plots /',len(list(TBL.glob('*.csv'))),'tables',
      'runtime',round(run_secs,2),'s', 'exact=',round(exact,5))
print('Pointing jitter 15 µrad: min diameter nom / robust (cm):',
      round(200*min_aperture_for_target(TARGET,15,link,rho=0),2),
      round(200*min_aperture_for_target(TARGET,15,link,rho=RHO),2))
print('Legacy exponential model break-even TV radius:',round(critical,6))
