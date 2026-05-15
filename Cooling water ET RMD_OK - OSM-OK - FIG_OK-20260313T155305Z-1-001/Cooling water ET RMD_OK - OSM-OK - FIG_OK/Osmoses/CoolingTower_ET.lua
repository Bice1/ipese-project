local osmose = require 'osmose'
local et = osmose.Model 'CoolingTower_ET'

et.header = {
    name = '',
    displayName = '',
    authors = {'Daniel Flórez-Orrego, EPFL IPESE research group'},
    developers = {''},
    contributors = {''},
    creation_date = '',
    updates = {''},
    versions = {'1.0'},
    confidentiality = {''},
    title = 'Cooling tower utility',
    description = [[Cooling tower utility]],
    references = {'Int. J. Environ. Sci. Tech., 5 (2), 251-262, Spring 2008; Perry Chemical Engineers Handbook'},
    adaptedwith = {},
    notes =  {}
  }


----------
-- User parameters
----------

et.inputs = {
    -- Heat 
    Cool_Tin = {default=12, unit='°C'},  -- T_supply, ECOS2105, Florez-Orrego, et al. initially 25
    Cool_Tout = {default=14, unit='°C'},  -- T_return, ECOS2105, Florez-Orrego, et al. initially 40
    Cool_Qmax = {default=100000, unit='kW'}, -- reference value of heat
    deltaH = {default=62.8, unit='kJ/kg'}, -- enthalpy change for cooling water @1 bar between 15 to 30°C
    Tdrybulb =  {default=20, unit='C'}, -- check the T dry bulb for each application
    RelatHum =  {default=40, unit='%'}, -- check the relat humidity for each application
    Twetbulb =  {default=12.17, unit='C'}, -- check the T wet bulb for each application
            
    -- Electricity consumption
    Cool_Elec = {default=0.021, unit='kW_el/kW_th' },-- MARLEY, Cooling Tower energy and its management. Energy for 400tons -30kW
    
    dtmin_gas={default = 8,unit = 'C'},
    dtmin_liq={default = 5,unit = 'C'},
    dtmin_2ph={default = 2,unit = 'C'},
------------------------------
------- ECONOMICS ------------
------------------------------
    
    n  = {default = 40, unit = 'year', description = 'Lifetime'},
    i  = {default = 0.06, unit = '-', description = 'interest rate'},
    CEPCI_2020  = {default = 596.2,    unit = '-', description = 'actual CEPCI'},
    CEPCI_2008  = {default = 575.4,    unit = '-', description = 'CEPCI 2008'},
}

-----------
-- Calculated parameters
-----------

et.outputs = {
    -- Electricity consumption
    E_ref_CT = {job='Cool_Elec*Cool_Qmax',unit='kW',},
    range = {job='Cool_Tout-Cool_Tin', unit='K'}, 
    approach = {job='Cool_Tin-Twetbulb', unit='K'}, 
    water_flow = {job='Cool_Qmax/deltaH*3600/1000', unit='t/h'}, -- water flow rate
    water_vflow = {job='water_flow()*1', unit='m^3/h'}, -- water volume flow rate for 1 t/m3
    watermu_CT = {job='0.00085*1.8*water_vflow()*(Cool_Tout-Cool_Tin)', unit='m3/h'}, -- makeup water in the CT system

------------------------------
------- ECONOMICS ------------
------------------------------ 
    Annuity = {job = '(i*(i+1)^n)/((i+1)^n-1)',unit = '-', },
    CTCost = {job = '746.49/0.066*(water_flow()^0.79)*(range()^0.57)*(approach()^-0.9924)*(0.022*Twetbulb+0.39)^2.447', unit = 'Eur'},
    Cinv2_CT = {job = 'CTCost()*(CEPCI_2020/CEPCI_2008)*Annuity()', unit = 'Eur/y'}, 
     

}

-----------
-- Layers
-----------

et:addLayers {Elec = {type= 'ResourceBalance', unit = 'kW'} }
et:addLayers {water = {type= 'ResourceBalance', unit = 'm^3/h'} } -- makeup water


-----------
-- Units
-----------

et:addUnit('CoolingTower',{type='Utility', Fmin = 0, Fmax = 100, Cost1=0, Cost2=0, Cinv1=0, Cinv2='Cinv2_CT'})
et['CoolingTower']:addStreams{
    -- Heat
    qt = qt({tin = 'Cool_Tin', hin = 0, tout='Cool_Tout', hout='Cool_Qmax', dtmin='dtmin_liq', alpha=1}),
    -- Electricity consumption
    elec_CT = rs({'Elec', 'in', 'E_ref_CT'}),
    -- Water makeup
    watermakeup_CT = rs({'water', 'in', 'watermu_CT'})
}

return et