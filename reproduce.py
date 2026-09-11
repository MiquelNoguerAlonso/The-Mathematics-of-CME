"""Reproduce the synthetic numerical results in The Mathematics of CME.

This is an implementation of the explicitly scoped models in the paper,
not an exchange simulator, decoder, or production margin calculator.
"""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal as D, ROUND_HALF_UP
import json
import platform
import hashlib
import numpy as np
import scipy
from scipy.optimize import linprog
from scipy.stats import poisson
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, FuncFormatter

ROOT = Path(__file__).resolve().parent
FIG = ROOT / 'figures'
FIG.mkdir(exist_ok=True)
NAVY, TEAL, GOLD, RED = '#17324e', '#178482', '#c68a24', '#bf5b51'
plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':10,
 'axes.titlesize':11, 'axes.labelsize':10, 'axes.spines.top':False,
 'axes.spines.right':False, 'axes.grid':True, 'grid.alpha':.16,
 'legend.frameon':False, 'savefig.dpi':240, 'figure.dpi':110,
 'text.parse_math':False, 'axes.formatter.useoffset':False})
results = {}

def check(name, actual, expected):
    if isinstance(expected, float):
        assert np.isclose(actual, expected, rtol=1e-10, atol=1e-8), (name, actual, expected)
    else:
        assert actual == expected, (name, actual, expected)
    results[name] = actual

def fifo(q, y):
    left = min(y, sum(q))
    out = []
    for qi in q:
        take = min(qi, left)
        out.append(take)
        left -= take
    return out

def pro_fifo(q, y, h=2):
    assert y >= 0 and h >= 1 and all(qi >= 0 for qi in q)
    total = sum(q)
    y = min(y, total)
    if not total:
        return [0]*len(q)
    if y == total:
        return list(q)
    ideals = [F(y*qi, total) for qi in q]
    base = [int(w) if int(w) >= h else 0 for w in ideals]
    extra = fifo([qi-bi for qi, bi in zip(q, base)], y-sum(base))
    return [bi+ei for bi, ei in zip(base, extra)]

def split_events(q, batches, allocator):
    remaining = list(q)
    total = [0]*len(q)
    events = []
    for batch in batches:
        fills = allocator(remaining, batch)
        remaining = [a-b for a,b in zip(remaining, fills)]
        total = [a+b for a,b in zip(total, fills)]
        events.append(fills)
    return total, remaining, events

def save(fig, name):
    fig.savefig(FIG/name, bbox_inches='tight', facecolor='white')
    plt.close(fig)

# 1. Allocation, including a threshold and event fragmentation.
q = [12,28,60]
ff, pf = fifo(q,37), pro_fifo(q,37)
check('allocation_fifo', ff, [12,25,0])
check('allocation_pro_fifo', pf, [5,10,22])
check('minimum_two', pro_fifo([2,3,5],4,2), [2,0,2])
check('minimum_one', pro_fifo([2,3,5],4,1), [1,1,2])
split = split_events([2,3,5],[2,2],pro_fifo)[0]
check('fragmented_aggressor', split, [2,2,0])
check('fifo_composition', split_events([2,3,5],[2,2],fifo)[0], fifo([2,3,5],4))
fig, axes = plt.subplots(1,2,figsize=(10.2,3.6),layout='constrained')
x=np.arange(3); width=.35
for ax, a, b, labels, title in [
 (axes[0],ff,pf,['FIFO','Pro rata + FIFO'],'37 contracts against (12, 28, 60)'),
 (axes[1],[2,0,2],split,['One event of 4','Two events of 2'],'Same total demand, different fills')]:
    ax.bar(x-width/2,a,width,color=NAVY,label=labels[0])
    ax.bar(x+width/2,b,width,color=TEAL,label=labels[1])
    ax.set(xticks=x,xticklabels=['Order 1','Order 2','Order 3'],ylabel='Contracts filled',title=title)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True)); ax.legend(loc='upper left',fontsize=8)
    ax.set_ylim(0,max(max(a),max(b))*1.3)
save(fig,'01_allocation.png')

# 2. Depth in ES quote units. Futures notional is not an upfront cash payment.
prices=[F(6000),F(24001,4),F(12001,2)]; sizes=[3,5,4]; m=50
def value_curve(y):
    return m*sum(pi*fi for pi,fi in zip(prices,fifo(sizes,y)))
value10=value_curve(10)
check('execution_value_10',str(value10),str(F(12000450,4)))
check('execution_average_10',float(value10/F(500)),6000.225)
check('execution_shortfall_10',float(value10-50*6000*10),112.5)
fig,axes=plt.subplots(1,2,figsize=(10.2,3.4),layout='constrained')
axes[0].stairs([0,.25,.5],[0,3,8,12],baseline=None,color=NAVY,linewidth=2)
axes[0].set(xlabel='Cumulative contracts',ylabel='Marginal price above 6000 (points)',title='The discrete depth curve')
ys=np.arange(13); costs=[float(value_curve(int(y))-50*6000*int(y)) for y in ys]
axes[1].plot(ys,costs,'o-',color=TEAL)
axes[1].scatter([10],[112.5],s=60,color=RED,zorder=4)
axes[1].annotate('$112.50 at 10 contracts',(10,112.5),xytext=(2,155),arrowprops={'arrowstyle':'->','color':RED},fontsize=9)
axes[1].set(xlabel='Contracts bought',ylabel='Shortfall against 6000 ($)',title='Multiplier-adjusted execution shortfall')
save(fig,'02_depth.png')

# 3. Two implied-IN recipes compete for the same A ask.
A=np.array([[1,1],[1,0],[0,1]],dtype=float); capacity=np.array([8,5,6.])
lp=linprog([-1,-1],A_ub=A,b_ub=capacity,bounds=(0,None),method='highs')
assert lp.success
check('implied_joint_capacity',float(-lp.fun),8.0)
check('implied_naive_sum',min(8,5)+min(8,6),11)
check('implied_feasible_5_3', (A@np.array([5,3])<=capacity).tolist(), [True]*3)
leg_matrix=np.array([[1,1],[-1,0],[0,-1]])
check('implied_leg_positions',(leg_matrix@np.array([5,3])).tolist(),[8,-5,-3])
spread_value=1000*(F('75.01')*8-F('74.81')*5-F('74.51')*3)
check('implied_quote_value',str(spread_value),'2500')
check('implied_out_price',str(F('.20')+F('74.82')),str(F('75.02')))
fig,axes=plt.subplots(1,2,figsize=(10.2,3.6),layout='constrained')
polygon=np.array([[0,0],[5,0],[5,3],[2,6],[0,6]])
axes[0].fill(polygon[:,0],polygon[:,1],color=TEAL,alpha=.22)
axes[0].plot([0,5,5,2,0,0],[0,0,3,6,6,0],color=TEAL)
axes[0].plot([2,5],[6,3],color=RED,linewidth=2,label='Shared A capacity: x₁ + x₂ = 8')
axes[0].scatter([5],[6],marker='x',color=RED,s=65,label='Individually feasible, jointly impossible')
axes[0].scatter([5],[3],color=NAVY,s=40)
axes[0].set(xlim=(-.3,6),ylim=(-.3,7),xlabel='A − B spread contracts',ylabel='A − C spread contracts',title='A resource polytope, not a rectangle')
axes[0].legend(fontsize=7,loc='upper left')
axes[1].bar(['A ask','B bid','C bid'],[8,5,6],color='#d8e1e7',label='Available')
axes[1].bar(['A ask','B bid','C bid'],[8,5,3],color=[NAVY,TEAL,GOLD],alpha=.85,label='Used by (5, 3)')
axes[1].set(ylabel='Underlying contracts',title='Shared resources are consumed once',ylim=(0,10));axes[1].legend(fontsize=8)
save(fig,'03_implied.png')

# 4. Embedded deterministic allocation and Poisson event times.
def completion_indices(allocator):
    remaining=list(q); indices=[None]*3
    for event in range(1,4):
        fill=allocator(remaining,37)
        remaining=[a-b for a,b in zip(remaining,fill)]
        for i,ri in enumerate(remaining):
            if ri==0 and indices[i] is None: indices[i]=event
    return indices
fi=completion_indices(fifo);pi=completion_indices(pro_fifo)
check('completion_event_fifo',fi,[1,2,3]);check('completion_event_pro_fifo',pi,[3,3,3])
check('mean_completion_fifo',[i/2 for i in fi],[.5,1,1.5])
check('mean_completion_pro_fifo',[i/2 for i in pi],[1.5,1.5,1.5])
fig,ax=plt.subplots(figsize=(8.2,3.7),layout='constrained');t=np.linspace(0,4,300)
for k,color in [(1,NAVY),(2,TEAL),(3,GOLD)]:
    ax.plot(t,poisson.sf(k-1,2*t),color=color,label=f'FIFO: order {k} (event {k})')
ax.plot(t,poisson.sf(2,2*t),'--',color=RED,linewidth=2,label='Pro rata + FIFO: all orders (event 3)')
ax.set(xlabel='Time (seconds)',ylabel='Probability of complete fill',title='Completion depends on allocation as well as arrival intensity',ylim=(0,1.03));ax.legend(fontsize=8)
save(fig,'04_completion.png')

# 5. IOP quantity and documented tie branches, excluding stop orders.
def auction_grid(bids,asks,candidates):
    B=[sum(q for p,q in bids if p>=c) for c in candidates]
    S=[sum(q for p,q in asks if p<=c) for c in candidates]
    return B,S,[min(b,s) for b,s in zip(B,S)],[b-s for b,s in zip(B,S)]
grid=[100,101,102,103]
bg,sg,vg,ig=auction_grid([(103,6),(102,4),(101,5)],[(100,4),(101,5),(102,3)],grid)
check('opening_B',bg,[15,15,10,6]);check('opening_S',sg,[4,9,12,12]);check('opening_volume',vg,[4,9,10,6]);check('opening_imbalance',ig,[11,6,-2,-6])
check('opening_price',grid[int(np.argmax(vg))],102)
check('opening_buy_fills',fifo([6,4],10),[6,4])
check('opening_sell_fills',fifo([4,5,3],10),[4,5,1])
cases=[('buy_only',[(103,6)],[(101,4)],[101,102,103],103),
 ('sell_only',[(103,4)],[(101,6)],[101,102,103],101),
 ('balanced',[(103,4)],[(101,4)],[101,102,103],102),
 ('both_signs',[(102,4),(101,2)],[(101,4),(102,3)],[101,102],101),
 ('zero_and_positive',[(102,4),(101,2)],[(101,4)],[101,102],102)]
case_results=[]
for name,b,s,p,expected in cases:
    B,S,V,I=auction_grid(b,s,p); eligible=[i for i,v in enumerate(V) if v==max(V)]
    if all(I[i]>0 for i in eligible): selected=max(p[i] for i in eligible)
    elif all(I[i]<0 for i in eligible): selected=min(p[i] for i in eligible)
    else:
        best=min(abs(I[i]) for i in eligible); remaining=[i for i in eligible if abs(I[i])==best]
        selected=min((p[i] for i in remaining),key=lambda price:abs(price-102))
    assert selected==expected
    case_results.append({'case':name,'prices':p,'B':B,'S':S,'V':V,'I':I,'selected':selected})
results['opening_tie_cases']=case_results
fig,axes=plt.subplots(1,2,figsize=(10.2,3.7),layout='constrained')
axes[0].step(grid,bg,where='mid',color=NAVY,label='Eligible buys')
axes[0].step(grid,sg,where='mid',color=TEAL,label='Eligible sells')
axes[0].plot(grid,vg,'o-',color=GOLD,label='Matched quantity')
axes[0].axvline(102,color=RED,linestyle='--');axes[0].set(xlabel='Candidate price',ylabel='Contracts',title='A unique primary maximizer',xticks=grid);axes[0].legend(fontsize=8)
axes[1].bar(grid,ig,color=[NAVY if v>=0 else RED for v in ig]);axes[1].axhline(0,color='black',linewidth=.7)
axes[1].set(xlabel='Candidate price',ylabel='Buy minus sell quantity',title='Imbalance at the same candidate prices',xticks=grid)
save(fig,'05_opening.png')

# 6. Settlement statistic, exact currency rounding and three-day cash ledger.
vwap=(F(6000)*4+F('6000.25')*2+F('6000.5')*4)/10
vwap_plus=(vwap*10+F(6001)*3)/13
check('settlement_vwap',float(vwap),6000.25)
check('settlement_vwap_added',str(vwap_plus),str(F(780055,130)))
def cash_value(p,multiplier=D(50)):
    return (D(str(p))*multiplier).quantize(D('.01'),rounding=ROUND_HALF_UP)
check('normal_rounding_positive',str(cash_value('1.005',D(1))),'1.01')
check('normal_rounding_negative',str(cash_value('-1.005',D(1))),'-1.01')
entry_trades=[(3,'6000'),(5,'6000.25'),(2,'6000.5')]
days=[('6001',entry_trades),('5998',[(-4,'6002')]),('6002',[(-6,'6003')])]
pos=0; prev=cash_value('6000'); cumulative=D(0); cash=D(12000); posted=D(0);ledger=[]
for day,(settle,trades) in enumerate(days,1):
    mark=cash_value(settle)
    variation=pos*(mark-prev)+sum(n*(mark-cash_value(p)) for n,p in trades)
    pos+=sum(n for n,p in trades)
    required=D(abs(pos)*1000)
    transfer=required-posted
    cash+=variation-transfer
    cumulative+=variation
    ledger.append({'day':day,'settlement':settle,'position':pos,'variation':str(variation),
      'margin_transfer':str(transfer),'posted_margin':str(required),'free_cash':str(cash),
      'cumulative_variation':str(cumulative)})
    posted=required;prev=mark
check('ledger_variation',[r['variation'] for r in ledger],['387.50','-700.00','1500.00'])
check('ledger_positions',[r['position'] for r in ledger],[10,6,0])
check('total_variation',str(cumulative),'1187.50')
check('terminal_cash',str(cash),'13187.50')
check('closed_trade_cash_identity',str(sum(-n*cash_value(p) for _,trades in days for n,p in trades)),'1187.50')
results['cash_ledger']=ledger
fig,axes=plt.subplots(1,2,figsize=(10.2,3.5),layout='constrained')
axes[0].bar([1,2,3],[float(r['variation']) for r in ledger],color=[TEAL,RED,TEAL]);axes[0].axhline(0,color='black',linewidth=.7)
axes[0].set(xticks=[1,2,3],xlabel='Clearing day',ylabel='Settlement variation ($)',title='Banked gains and losses')
axes[1].plot([0,1,2,3],[12000]+[float(r['free_cash']) for r in ledger],'o-',color=NAVY,label='Free cash')
axes[1].plot([0,1,2,3],[0]+[float(r['posted_margin']) for r in ledger],'s-',color=GOLD,label='Posted margin')
axes[1].set(xticks=[0,1,2,3],xlabel='Clearing day',ylabel='Dollars',title='Collateral transfers preserve total equity');axes[1].legend(fontsize=8)
save(fig,'06_settlement.png')

# 7. A declared convex scenario illustration, deliberately distinct from SPAN 2.
loss_vectors=np.array([[2000,2000],[-2000,-2000],[1000,-1000],[-1000,1000],[3000,1000],[-3000,-1000]])
def risk(z): return max(0.,float(np.max(loss_vectors@np.array(z))))
def margin(z):
    gross=sum(abs(float(zi)) for zi in z)
    return risk(z)+100*gross+50*max(gross-8,0)**2
losses=(loss_vectors@np.array([5,-5])).tolist()
check('spread_scenario_losses',losses,[0,0,10000,-10000,10000,-10000])
check('spread_risk',risk([5,-5]),10000.)
check('standalone_sum',risk([5,0])+risk([0,-5]),25000.)
check('spread_margin',margin([5,-5]),11200.)
check('partial_hedge_removal_margin',margin([5,-3]),12800.)
partial=(loss_vectors@np.array([5,-3])).tolist()
check('partial_hedge_losses',partial,[4000,-4000,8000,-8000,12000,-12000])
check('tail_mean_top_two',float(np.mean(sorted(partial)[-2:])),10000.)
check('empirical_var_two_thirds',sorted(partial)[3],4000)
fig,axes=plt.subplots(1,2,figsize=(10.2,4.0),layout='constrained')
xx,yy=np.meshgrid(np.linspace(-6,6,181),np.linspace(-6,6,181))
rr=np.maximum.reduce([2000*np.abs(xx+yy),1000*np.abs(xx-yy),1000*np.abs(3*xx+yy)])
cont=axes[0].contour(xx,yy,rr,levels=[4000,8000,12000,16000,20000],colors=[TEAL,NAVY,GOLD,RED,'#777777'])
axes[0].clabel(cont,fmt=lambda v:f'${v/1000:g}k',fontsize=8)
axes[0].scatter([5,5],[-5,-3],color=[TEAL,RED],s=40)
axes[0].annotate('',(5,-3),(5,-5),arrowprops={'arrowstyle':'->','color':RED})
axes[0].set(xlabel='Position in A',ylabel='Position in B',title='Scenario-risk contours');axes[0].set_aspect('equal')
inds=np.arange(6)
axes[1].bar(inds-.18,np.array(losses)/1000,.36,color=TEAL,label='(5, −5)')
axes[1].bar(inds+.18,np.array(partial)/1000,.36,color=RED,label='(5, −3)')
axes[1].axhline(0,color='black',linewidth=.7);axes[1].set(xticks=inds,xticklabels=['1','2','3','4','5','6'],xlabel='Scenario',ylabel='Portfolio loss ($ thousands)',title='Removing a hedge raises worst loss');axes[1].legend(fontsize=8)
save(fig,'07_margin.png')

# 8. Prefix funding and asset eligibility. All collateral parameters are synthetic.
path_a=np.array([6000,5980,6004]);path_b=np.array([6000,6002,6004]);position=10
ca=(path_a-path_a[0])*50*position;cb=(path_b-path_b[0])*50*position
margin_increment=np.array([0,5000,0])
resource_a=ca-margin_increment
check('funding_path_a',int(max(0,-min(ca))),10000)
check('funding_path_b',int(max(0,-min(cb))),0)
check('funding_with_margin_shock',int(max(0,-min(resource_a))),15000)
check('funding_shortfall_from_8000',int(max(0,-min(resource_a))-8000),7000)
cash_supply=5000;bond_supply=20000;haircut=.10;im=10800
check('collateral_total_credit',cash_supply+(1-haircut)*bond_supply,23000.)
check('collateral_aggregate_test',6000+im<=23000,True)
check('collateral_cash_feasible',6000<=cash_supply,False)
check('collateral_feasible_bond_principal',im/(1-haircut),12000.)
fig,axes=plt.subplots(1,2,figsize=(10.2,3.5),layout='constrained')
for y,c,l in [(ca/1000,NAVY,'Path A: variation only'),(cb/1000,TEAL,'Path B: variation only'),(resource_a/1000,RED,'Path A: variation minus extra margin')]:
    axes[0].plot([0,1,2],y,'o-',color=c,label=l)
axes[0].axhline(0,color='black',linewidth=.7);axes[0].set(xticks=[0,1,2],xlabel='Settlement cycle',ylabel='Cumulative available cash change ($k)',title='Equal terminal P&L, unequal funding');axes[0].legend(fontsize=7)
axes[1].bar(['All credited\nassets','IM + VM\nrequirements','Cash\navailable','VM cash\nrequired'],[23,16.8,5,6],color=[TEAL,GOLD,NAVY,RED])
axes[1].set(ylabel='Dollars (thousands)',title='Aggregate coverage misses the cash bottleneck')
save(fig,'08_funding.png')

# 9. Delivery invoice and an exercised option on a future.
names=['A','B','C'];clean=[D('99'),D('101'),D('98')];cf=[D('.90'),D('.92'),D('.88')];ai=[D('600'),D('800'),D('500')]
invoices=[(D(1000)*D(110)*c).quantize(D('.01'),rounding=ROUND_HALF_UP)+a for c,a in zip(cf,ai)]
net=[D(1000)*p+a-inv for p,a,inv in zip(clean,ai,invoices)]
check('delivery_invoices',[str(v) for v in invoices],['99600.00','102000.00','97300.00'])
check('delivery_net_costs',[str(v) for v in net],['0.00','-200.00','1200.00'])
check('cheapest_to_deliver',names[int(np.argmin(net))],'B')
check('delivery_switch_AB',float((clean[1]-clean[0])/(cf[1]-cf[0])),100.)
premium=D('18.00')*50;exercise_vm=2*50*(D(6030)-D(6000));net_option=exercise_vm-2*premium
check('option_premium_paid',str(-2*premium),'-1800.00')
check('option_exercise_variation',str(exercise_vm),'3000')
check('option_net_through_exercise',str(net_option),'1200.00')
fig,axes=plt.subplots(1,2,figsize=(10.2,3.7),layout='constrained')
fs=np.linspace(95,115,200)
lines=[]
for n,p,c,color in zip(names,clean,cf,[NAVY,TEAL,GOLD]):
    line=1000*(float(p)-fs*float(c))-1000*(float(clean[0])-fs*float(cf[0]));lines.append(line)
    axes[0].plot(fs,line,label=f'Deliverable {n}',color=color)
axes[0].plot(fs,np.min(lines,axis=0),'--',color=RED,label='Minimum delivery cost')
axes[0].axvline(100,color='#777777',linestyle=':',linewidth=1)
axes[0].set(xlabel='Futures invoice price (points)',ylabel='Delivery cost relative to A ($)',title='A change in the cheapest deliverable');axes[0].legend(fontsize=8)
underlying=np.linspace(5940,6080,201)
axes[1].plot(underlying,100*np.maximum(underlying-6000,0)-1800,color=NAVY,linewidth=2)
axes[1].scatter([6030],[1200],color=TEAL,s=45);axes[1].axhline(0,color='#777777',linewidth=.8)
axes[1].set(xlabel='Underlying future at exercise/expiry',ylabel='Two-call payoff less premium ($)',title='Exercise creates a futures ledger entry')
save(fig,'09_delivery_options.png')

# 10. A stylized waterfall conserves losses by layer.
def waterfall(loss, resources):
    remaining=loss;used=[]
    for capacity in resources:
        draw=min(remaining,capacity);used.append(draw);remaining-=draw
    return used,remaining
used,residual=waterfall(17,[8,2,5,4])
check('waterfall_draws',used,[8,2,5,2]);check('waterfall_residual',residual,0)
assert sum(used)+residual==17

# Exact invariant checks over a bounded collection of economically distinct ledgers.
for quantities in ([2,3,5],[12,28,60],[1,1,1],[1,9,90]):
    for demand in (0,1,2,4,7,37,101):
        for threshold in (1,2,3):
            fill=pro_fifo(quantities,demand,threshold)
            assert sum(fill)==min(demand,sum(quantities))
            assert all(0<=f<=v for f,v in zip(fill,quantities))
            y=min(demand,sum(quantities))
            ideal=[F(y*v,sum(quantities)) for v in quantities]
            base=[int(w) if int(w)>=threshold else 0 for w in ideal]
            residual=y-sum(base)
            assert residual<threshold*len(quantities)
            assert sum(abs(F(f)-w) for f,w in zip(fill,ideal))<=2*residual
results['allocation_invariants']='84 quantity/demand/threshold combinations passed'

def encode(value):
    if isinstance(value,(np.integer,np.floating)):return value.item()
    raise TypeError(type(value))
(ROOT/'results.json').write_text(json.dumps(results,indent=2,default=encode)+'\n')
(ROOT/'environment.json').write_text(json.dumps({'python':platform.python_version(),
 'numpy':np.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__,
 'figure_count':len(list(FIG.glob('*.png'))),'random_sampling':False},indent=2)+'\n')
print(f'{len(results)} numerical result groups verified; {len(list(FIG.glob("*.png")))} figures written.')
