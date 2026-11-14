"""Create real-data figures from analyze_retail.py outputs (no synthetic observations)."""
from pathlib import Path
import sys,os,json
ROOT=Path(__file__).resolve().parents[1]
if (ROOT/'.plot-deps').exists():sys.path.insert(0,str(ROOT/'.plot-deps'))
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.mpl-cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import pandas as pd
import numpy as np
DATA=ROOT/'projects/retail-data';OUT=ROOT/'assets/retail';OUT.mkdir(parents=True,exist_ok=True)
s=json.loads((DATA/'summary.json').read_text(encoding='utf8'))
monthly=pd.read_csv(DATA/'monthly.csv');countries=pd.DataFrame(s['overseas_eligible'])
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none','svg.hashsalt':'retail-real-data','axes.spines.top':False,'axes.spines.right':False})
INK='#252a2a';GOLD='#a38a58';GREEN='#527269';GRAY='#b7b9b3';PAPER='#faf9f5';MUTED='#656963';LINE='#e3e3dc'
def base(title,subtitle,height=5.5):
    fig,ax=plt.subplots(figsize=(11,height));fig.set_facecolor(PAPER);ax.set_facecolor(PAPER)
    fig.subplots_adjust(left=.14,right=.95,top=.73,bottom=.18)
    fig.text(.055,.93,title,fontsize=19,weight='bold',color=INK)
    fig.text(.055,.865,subtitle,fontsize=10,color=MUTED)
    for spine in ax.spines.values():spine.set_visible(False)
    ax.tick_params(length=0,pad=10,colors=MUTED)
    return fig,ax
def save(fig,name,note):
    fig.text(.055,.045,note,fontsize=9,color=MUTED)
    fig.savefig(OUT/f'{name}.svg',facecolor=PAPER,metadata={'Date':None})
    fig.savefig(OUT/f'{name}.png',facecolor=PAPER,dpi=150)
    plt.close(fig)

fig,ax=base('Most months are quiet. One month needs a closer look.',
            'Monthly product credit amount | Dec 2009 - Nov 2011 | GBP',6)
x=np.arange(len(monthly));v=monthly.credit.to_numpy();idx=monthly.index[monthly.month.eq('2011-01')][0]
ax.bar(x,v,color=GRAY,width=.7,zorder=3)
ax.bar(idx,s['january_extreme']['amount'],bottom=v[idx]-s['january_extreme']['amount'],color=GOLD,width=.7,zorder=4)
ax.set_ylim(0,112000);ax.grid(axis='y',color=LINE,zorder=0)
ax.set_xticks(x[::3],monthly.month.iloc[::3],rotation=0,fontsize=9)
ax.yaxis.set_major_formatter(FuncFormatter(lambda value,pos:f'{value/1000:.0f}k'))
ax.annotate('Jan 2011: '+f'GBP {v[idx]:,.0f}',xy=(idx,v[idx]),xytext=(idx+1,101000),fontsize=11,color=INK,
            arrowprops={'arrowstyle':'-','color':GOLD},ha='left')
ax.text(.02,.88,'Gold = one same-day matched credit\n'+f"GBP {s['january_extreme']['amount']:,.0f} / {s['january_extreme']['share_january_credit_pct']:.1f}% of the month",transform=ax.transAxes,fontsize=10,color='#76613c')
save(fig,'monthly','Source: UCI Online Retail II. Credit entries are not necessarily physical returns.')

countries=countries.sort_values('screened_ratio_pct',ascending=False).reset_index(drop=True)
fig,ax=base('Look at both the amount and the transaction pattern.',
            'Overseas markets with at least GBP 100,000 in recorded product sales',6)
fig.subplots_adjust(left=.18)
y=np.arange(len(countries))
ax.barh(y-.16,countries.credit_ratio_pct,height=.27,color=GRAY,label='All product credits',zorder=3)
ax.barh(y+.16,countries.screened_ratio_pct,height=.27,color=GREEN,label='Without same-day candidates',zorder=3)
for i,row in countries.iterrows():
    ax.text(row.credit_ratio_pct+.09,i-.16,f'{row.credit_ratio_pct:.2f}%',va='center',fontsize=10,color=MUTED)
    ax.text(row.screened_ratio_pct+.09,i+.16,f'{row.screened_ratio_pct:.2f}%',va='center',fontsize=10,color=GREEN)
ax.set_yticks(y,countries.Country.replace({'EIRE':'Ireland (EIRE)'}));ax.invert_yaxis();ax.set_xlim(0,7)
ax.xaxis.set_major_formatter(FuncFormatter(lambda value,pos:f'{value:.0f}%'))
ax.grid(axis='x',color=LINE,zorder=0);ax.legend(loc='lower left',bbox_to_anchor=(0,1.02),ncol=2,frameon=False,fontsize=9)
save(fig,'markets','Credit amount / recorded sales. Sales denominator unchanged. Screening only, not a corrected return rate.')

f=s['france_focus']; share=f['share_country_credit_pct'];rest=f['country_credit']-f['credit']
fig,ax=base('One credit invoice explains 67.8% of France\'s credits.',
            'France product credit amount | GBP 17,514.39 across the 24-month window',4.4)
ax.barh(0,share,color=GOLD,height=.42)
ax.barh(0,100-share,left=share,color='#d9d9d2',height=.42)
ax.text(share/2,0,f"Invoice {f['invoice']}\nGBP {f['credit']:,.2f}\n{share:.1f}%",ha='center',va='center',fontsize=12,color=INK)
ax.text(share+(100-share)/2,0,f"Other invoices\nGBP {rest:,.2f}\n{100-share:.1f}%",ha='center',va='center',fontsize=11,color=INK)
ax.set_xlim(0,100);ax.set_ylim(-.5,.5);ax.set_yticks([]);ax.set_xticks([0,25,50,75,100],['0%','25%','50%','75%','100%'])
save(fig,'france','45 product lines in one invoice. Concentration is evidence for investigation, not proof of product defects.')

fig,ax=base('The pattern survives a duplicate-row sensitivity check.',
            'Credit amount / recorded sales | baseline vs within-sheet exact duplicates collapsed',4.8)
labels=['All markets','France'];b=[s['credit_ratio_pct'],0]
fr_country=next(r for r in s['overseas_eligible'] if r['Country']=='France')
b[1]=fr_country['credit_ratio_pct'];d=[s['dedup_ratio_pct'],fr_country['dedup_credit_ratio_pct']]
y=np.arange(2)
ax.barh(y-.16,b,height=.28,color=INK,label='Baseline',zorder=3)
ax.barh(y+.16,d,height=.28,color=GOLD,label='Duplicate-collapse sensitivity',zorder=3)
for i in range(2):
    ax.text(b[i]+.1,y[i]-.16,f'{b[i]:.3f}%',va='center',fontsize=10)
    ax.text(d[i]+.1,y[i]+.16,f'{d[i]:.3f}%',va='center',fontsize=10)
ax.set_yticks(y,labels);ax.invert_yaxis();ax.set_xlim(0,7.5);ax.grid(axis='x',color=LINE,zorder=0)
ax.xaxis.set_major_formatter(FuncFormatter(lambda v,p:f'{v:.0f}%'));ax.legend(frameon=False,loc='lower left',bbox_to_anchor=(0,1.02),ncol=2,fontsize=9)
save(fig,'sensitivity','Within-sheet duplicates are ambiguous. Baseline preserves them; cross-sheet copies are removed in both views.')
print('Created 4 SVG and PNG charts from verified aggregate data.')
