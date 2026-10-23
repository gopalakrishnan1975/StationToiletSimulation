from math import ceil

def staffing(blocks=3,shifts=3,cleaners_per_block_shift=1,peak_extra=6,supervisors=4,relief_factor=1.30,monthly_cleaner=30000,monthly_supervisor=40000):
    continuous_posts=blocks*shifts*cleaners_per_block_shift
    # Peak-extra represents establishment positions, not 24h posts.
    cleaners=ceil(continuous_posts*relief_factor)+peak_extra
    return {'continuous_posts':continuous_posts,'cleaner_establishment':cleaners,'supervisors':supervisors,'total_staff':cleaners+supervisors,'annual_staff_lakh':round((cleaners*monthly_cleaner+supervisors*monthly_supervisor)*12/100000,2),'note':'Confirm weekly offs, shift duration, peak deployment, wage compliance and female-facility staffing.'}
