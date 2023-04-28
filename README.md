# GetNaturalGasRegulatoryRates
Playing around with emailing up-to-date Natural Gas Rates Fluctuations

This came from being on a floating natural gas rate and wanting to know exactly when the rates are changing and what the rate is going to. I built this script and it is scheduled to check daily via microsoft task scheduler and email me when the rates change. it then writes a .txt file to to the folder so the task scheduler doesnt trigger an emial every day. 

# TODO: Clean up the script a bit and make it more dynamic with its pathing
# TODO: Create some temp files instead of writing to the repo root
# TODO: Maybe build the emial to be a formatted table for both the most current year's floating Natural Gas Rate and Electricity rates.
