"""Generate fully reproducible results; launch: python run_study.py.

All generated artifacts go under results/; no figure is hand-edited.
"""
import os,sys,json,csv,math,time,platform,hashlib
from pathlib import Path
import numpy as np
import scipy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from cycler import cycler
from dataclasses import asdict, replace
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from atmosphere import (PAPER_EXPONENTIAL,DB_LABEL,scenarios_1550nm,exact_distribution,
                        transmittance_from_q)
from fso_link import (Link,SCENARIO_NAMES,DEFAULT_PRIOR,gaussian_aperture_capture,
    capture_via_independent_quadrature,mean_capture_analytic,conditional_availability,
    availability,worst_case_tv_greedy,worst_case_tv_lp,min_aperture_for_target,
    sample_link,wilson_score,weather_limited_ceiling,critical_tv_radius)

OUT=ROOT/'results'; FIG=OUT/'figures'; TBL=OUT/'tables'; META=OUT/'metadata'
for d in (FIG,TBL,META):d.mkdir(parents=True,exist_ok=True)
link=Link()
SEED=20261123
TARGET=.92
RHO=.04
FAST=os.environ.get('FAST_MODE','1') != '0'
N_MC=20000 if FAST else 100000
DPI=165
plt.rcParams.update({
    'figure.dpi':125, 'savefig.dpi':DPI, 'font.family':'DejaVu Sans',
    'font.size':10, 'axes.titlesize':11.5, 'axes.titleweight':'medium',
    'axes.labelsize':9.5, 'axes.labelcolor':'#334155', 'text.color':'#1F3443',
    'axes.edgecolor':'#BBCBD4', 'xtick.color':'#586F7D', 'ytick.color':'#586F7D',
    'axes.spines.top':False, 'axes.spines.right':False,
    'axes.prop_cycle':cycler(color=['#158A88','#D39742','#577DB6','#8466AC','#D76A66','#4D9782']),
    'grid.color':'#E3EAEF', 'grid.alpha':.65,
    'legend.frameon':False, 'figure.facecolor':'white',
    'axes.facecolor':'white', 'savefig.facecolor':'white'
})
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
radii=np.linspace(.06,.30,55)
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
plt.ylim(.70,1.00);plt.legend(loc='lower right',ncol=2,fontsize=7)
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
plt.text(.98,.08,'TV radius 8%: globally infeasible\nfor the 92% target',
         transform=plt.gca().transAxes,ha='right',va='bottom',fontsize=8)
plt.legend(fontsize=9);savefig('04_minimum_aperture_frontier')

# 05: uncertainty sensitivity at fixed hardware, includes exact LP reference
jitter=15; ap=.14
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
plt.ylim(.77,1);plt.legend(fontsize=8);savefig('05_weather_probability_shift')
csvout('03_tv_radius_sensitivity.csv',['TV_radius','worst_case_availability'],zip(rad,values))

# 06: feasibility heat map across TV radius and aperture
rho_grid=np.linspace(0,.10,24)
ap_grid=np.linspace(.08,.26,35)
mat=np.array([[availability(a,15,link,rho=rr) for a in ap_grid] for rr in rho_grid])
fig,ax=plt.subplots(figsize=(8.1,5.0))
im=ax.imshow(mat,origin='lower',aspect='auto',cmap='viridis',extent=[ap_grid[0]*200,ap_grid[-1]*200,rho_grid[0],rho_grid[-1]],vmin=.80,vmax=.97)
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
    # Clear-only atmospheric scenario but with stochastic pointing jitter
    point_only=float(conditional_availability(a,15,link)[0])
    ablation.append((a,joint,weather_only,point_only))
csvout('04_ablation.csv',['aperture_radius_m','joint_weather_and_pointing','weather_only_zero_jitter','clear_scenario_pointing_only'],ablation)
plt.figure(figsize=(8,4.7))
for ii,label in [(1,'Joint: weather + pointing'),(2,'Weather mixture; no jitter'),(3,'Clear-scenario propagation + jitter')]:
    plt.plot(radii*200,[row[ii] for row in ablation],label=label)
plt.axhline(TARGET,ls=':',color='grey')
plt.xlabel('Receiver aperture diameter (cm)');plt.ylabel('Nominal optical-power availability')
plt.title('07 | Ablation: weather state and pointing both matter')
plt.ylim(.45,1.01);plt.legend(fontsize=8);savefig('07_ablation')

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

# 09: exact atmospheric ceiling / global feasibility certificate
rho_l=np.linspace(0,.11,90)
caps=np.array([weather_limited_ceiling(link,rho=float(z))[0] for z in rho_l])
critical=critical_tv_radius(TARGET,link)
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
plt.title('09 | A global feasibility certificate: aperture cannot fix weather extinction')
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
    'propagation_convention_primary':PAPER_EXPONENTIAL,
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
paths=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='manifest.json')
manifest={'files':[{'path':str(p.relative_to(OUT)), 'bytes':p.stat().st_size,
    'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]}
(META/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
print('RESULTS_READY',len(list(FIG.glob('*.png'))),'plots /',len(list(TBL.glob('*.csv'))),'tables',
      'runtime',round(run_secs,2),'s', 'exact=',round(exact,5))
print('Pointing jitter 15 µrad: min diameter nom / robust (cm):',
      round(200*min_aperture_for_target(TARGET,15,link,rho=0),2),
      round(200*min_aperture_for_target(TARGET,15,link,rho=RHO),2))
print('Exact model global TV feasibility radius:',round(critical,6))
