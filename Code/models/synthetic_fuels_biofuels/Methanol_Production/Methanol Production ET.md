---
title: "Methanol Production from Syngas — Energy Technology Model"
subtitle: "IEA IETS Task XXIV · Subtask 1 · Activity 3.1 (Energy Technologies)"
author: "Daniel Flórez-Orrego, Meire Domingos — EPFL IPESE"
date: "2025-12-11"
---

# Methanol production from syngas

A grey-box, steady-state model of a **catalytic methanol-synthesis plant** fed with a purified, H₂-rich syngas (molar H₂/CO ≈ 2/1). The unit covers the **two-stage syngas compression** (from 35 bar to the reactor pressure of about 90 bar), the **isothermal fixed-bed catalytic reactor** (CO + 2 H₂ → CH₃OH and CO₂ + 3 H₂ → CH₃OH + H₂O at ~210 °C), the **reactor-effluent cooling and flash separation**, the **methanol distillation column**, and the **purge-gas flaring**. The model exposes a syngas input, an electricity input, a marketable methanol output, a CO₂-in-flue-gas output, and 14 heat streams that together represent the cycle's preheating, intercooling, reaction, condensation, reboiling, and flaring duties.

**Variants.** Two further configurations are documented in the underlying model set: `MeOH_withcomp35to90_ET` (explicit 35 → 90 bar compression train) and its `_MASBook` variant for the EPFL Master-of-Advanced-Studies course book. The process topology, parameter groups, and interfaces are the same across variants; only the inlet pressure and the intercooling temperatures differ.

## 1. Model card

| Field | Value |
|:------|:------|
| Model identifier | Methanol Production (ET) |
| Authors | Daniel Flórez-Orrego, Meire Domingos — EPFL IPESE |
| Contact | daniel.florezorrego@epfl.ch · oktay.boztas@epfl.ch |
| Version · Status | 1 · Maintained |
| Created · Updated | 2025-12-11 · 2025-12-11 |
| Confidentiality · Sharing layer | Open · 1 (fully shareable) |
| Model grade · TRL | Gray-box · 9 |
| Reference capacity | 12 102.8 kg/h of methanol (≈ 75 MW LHV) |
| Keywords | Methanol Production · Syngas · Distillation · Reactor · Compressor |
| Description | Methanol production from purified syngas with molar H₂/CO ≈ 2/1 |

## 2. Process description

Methanol is one of the leading platform chemicals of the energy transition: a liquid hydrogen carrier produced from H₂ and a carbon source (CO or CO₂), storable, transportable, and convertible into fuels (DME, gasoline, SAF), olefins, formaldehyde, and many other downstream products. The dominant industrial route is the **low-pressure Cu/ZnO/Al₂O₃-catalysed synthesis** from a purified, H₂-rich syngas, conducted at 50–100 bar and 200–270 °C in a fixed-bed isothermal reactor:

$$\mathrm{CO + 2H_2 \rightleftharpoons CH_3OH}, \quad \Delta H^\circ_{rxn} \approx -90\ \mathrm{kJ/mol\ (exothermic)};$$
$$\mathrm{CO_2 + 3H_2 \rightleftharpoons CH_3OH + H_2O}, \quad \Delta H^\circ_{rxn} \approx -49\ \mathrm{kJ/mol\ (exothermic)};$$
$$\mathrm{CO_2 + H_2 \rightleftharpoons CO + H_2O}\quad \text{(reverse water-gas shift, mildly endothermic).}$$

The reactor is operated **isothermally** by withdrawing heat from the catalyst bed at a useful temperature (typically 200–250 °C, here 210 °C); this heat duty is one of the dominant streams the cycle exposes to the surrounding system. The reactor effluent is cooled, the unreacted syngas is flashed off and recycled to the compressor, and the condensed crude methanol is sent to a **distillation column** that removes water, methanol, and dissolved gases. The light non-condensables — together with the recycle purge — are sent to a **flare** that operates at ~1 000 °C and produces a CO₂-laden flue gas as the only external emission.

The model is **calibrated** to a fixed Hysys-simulation operating point (reactor pressure 90 bar, reactor temperature 210 °C, two compression stages 35 → ~60 → 90 bar with intercooling, distillation at ~1 bar). All operating temperatures, heat duties, and compressor powers are boundary parameters; the optimisation degrees of freedom are limited to the unit's overall capacity multiplier and its match against the surrounding system on the heat cascade.

## 3. Block flow diagram

![Methanol production plant: syngas compression (35 → 90 bar), isothermal catalytic reactor at 210 °C, reactor-effluent cooling, flash separation, distillation (condenser 54 °C, reboiler 67 °C), and purge-gas flaring at 1 000 °C.](../Figures/MeohProduction.svg){width=85%}

## 4. Parameters

All parameters in the source model are **boundary values** (operating points fixed by the Hysys-simulation calibration). Capacity-related quantities and CEPCI / financial assumptions are listed under boundary, and the cost-correlation reference values under literature.

### 4.1 Boundary (operating point)

| Group | Parameter | Symbol | Default | Unit |
|:------|:----------|:-------|--------:|:-----|
| Syngas compression — stage 1 | inlet T → outlet T, duty / power | $T_{h1,in}/T_{h1,out}/Q_{h1}$, $W_{c1}$ | 86 / 35 / 532.9, 611.2 | °C / kW |
| Syngas compression — stage 2 | inlet T → outlet T, duty / power | $T_{h2,in}/T_{h2,out}/Q_{h2}$, $W_{c2}$ | 97 / 35 / 651.5, 635.2 | °C / kW |
| Preheating before reactor — 1st stage | $T_{c1,in}/T_{c1,out}/Q_{c1}$ | 64 / 175 / 1 815.7 | °C / kW |
| Preheating before reactor — 2nd stage | $T_{c2,in}/T_{c2,out}/Q_{c2}$ | 175 / 210 / 575.5 | °C / kW |
| Reactor effluent cooling | $T_{h5,in}/T_{h5,out}/Q_{h5}$ | 210 / 153 / 1 815.7 | °C / kW |
| Reactor isothermal cooling (reaction heat) | $T_{h7}/Q_{h7}$ | 210 (isothermal) / 10 746 | °C / kW |
| Preflash cooling | $T_{h6,in}/T_{h6,out}/Q_{h6}$ | 134 / 30 / 4 192 | °C / kW |
| Distillation condenser | $T_{h8}/Q_{h8}$ | 54 (isothermal) / 5 324.7 | °C / kW |
| Distillation reboiler | $T_{h9}/Q_{h9}$ | 67 (isothermal) / 5 643.5 | °C / kW |
| Product cooling — condenser effluent | $T_{h11,in}/T_{h11,out}/Q_{h11}$ | 54 / 25 / 344.7 | °C / kW |
| Product cooling — bottoms effluent | $T_{h12,in}/T_{h12,out}/Q_{h12}$ | 67 / 25 / 2.65 | °C / kW |
| Auxiliary cooler (preflash) | $T_{h10}/Q_{h10}$ | 30 (isothermal) / 12.5 | °C / kW |
| Purge-gas flaring — stage 1 | $T_{h13}/Q_{h13}$ | 1 000 (isothermal) / 3 634 | °C / kW |
| Purge-gas flaring — stage 2 | $T_{h14,in}/T_{h14,out}/Q_{h14}$ | 1 000 / 150 / 2 190 | °C / kW |
| Methanol recirculator pump | $W_{c5}$ | 479.6 | kW |
| Syngas mass flow consumed | $\dot m_{syngas}$ | 14 247.7 | kg/h |
| Methanol mass flow produced | $\dot m_{MeOH}$ | 12 102.8 | kg/h |
| CO₂ in flare stack | $\dot m_{CO_2,stack}$ | 1 093.2 | kg/h |
| $\Delta T_{min}$ — gas / liquid / two-phase | $\Delta T_{min,gas/liq/2ph}$ | 8 / 5 / 2 | °C |
| Equipment lifetime | $n$ | 40 | year |
| Interest rate | $i$ | 0.06 | – |
| CEPCI 2022 | $CEPCI_{2022}$ | 816 | – |

### 4.2 Literature

| Parameter | Symbol | Default | Unit | Source |
|:----------|:-------|--------:|:-----|:-------|
| Methanol LHV | $LHV_{MeOH}$ | 22 400 | kJ/kg | Domingos *et al.* (see [1]) |
| Reference plant investment cost | $C_{base}$ | 18 300 000 | EUR (2022) | [1] |
| Reference plant capacity | $\dot Q_{base}$ | 30 200 | kW (LHV) | [1] |
| Scaling exponent | $sc$ | 0.8 | – | [1] |

## 5. Derived quantities at the reference operating point

| Quantity | Symbol | Expression | Value | Unit |
|:---------|:-------|:-----------|------:|:-----|
| Methanol energy output (LHV) | $\dot Q_{MeOH}$ | $\dot m_{MeOH}\,LHV_{MeOH}/3600$ | 75 306 | kW |
| Total electricity demand | $W_{tot}$ | $W_{c1}+W_{c2}+W_{c5}$ | 1 726 | kW |
| Annualisation factor | $a$ | $i(1+i)^{n}/((1+i)^{n}-1)$ | 0.0665 | – |
| Annualised investment cost | $C_{inv2,MeOH}$ | $C_{base}\,(\dot Q_{MeOH}/\dot Q_{base})^{sc}\,a$ | 2.53 M | EUR/y |

The investment cost uses a **size-scaling** correlation in the methanol energy output: $C_{inv} = C_{base}\,(\dot Q_{MeOH}/\dot Q_{base})^{sc}$, with $sc = 0.8$ (typical "six-tenths-rule" exponent for chemical plants).

## 6. Interfaces and heat streams

The methanol plant exchanges four resources with the surrounding system and exposes 14 thermal streams.

| Interface | Direction / Type | Reference flow | T | P | Phase / Composition |
|:----------|:-----------------|---------------:|:--|:--|:--------------------|
| Syngas feed | In · Mass | 14 247.7 kg/h | 25 °C | 35 bar | Vapour, molar H₂/CO ≈ 0.642 / 0.313 |
| Electricity (compressors + circulator) | In · Electrical | 1 726 kW | – | – | – |
| Methanol product | Out · Mass | 12 102.8 kg/h | 25 °C | 1 bar | Liquid, CH₃OH (100 %) |
| CO₂ in flue gas (flare) | Out · Mass (emission) | 1 093.2 kg/h | 150 °C | 1 bar | Vapour, CO₂ (100 %) |

**Heat streams** ($\Delta T_{min}/2 = 4$ °C for gases, 1 °C for two-phase). Source-data labels (Hot / Cold) and duties are reproduced as given.

| Name | Source label | Temperature range | Duty (kW) | Role |
|:-----|:-------------|:------------------|----------:|:-----|
| qt_c110 | Cold | 64 °C → 175 °C | 1 815.7 | Feed preheating (1st stage) |
| qt_c111 | Cold | 175 °C → 210 °C | 575.5 | Feed preheating (2nd stage, to reactor inlet) |
| qt_h118 | Hot | 86 °C → 35 °C | 532.9 | Syngas compressor — stage-1 intercooling |
| qt_h119 | Hot | 97 °C → 35 °C | 651.5 | Syngas compressor — stage-2 intercooling |
| qt_h122 | Hot | 210 °C → 153 °C | 1 815.7 | Reactor effluent sensible cooling |
| qt_h123 | Hot | 134 °C → 30 °C | 4 192 | Preflash cooling (partial condensation) |
| qt_h124 | Hot | 210 °C (isothermal) | 10 746 | **Reactor isothermal cooling** (synthesis heat of reaction) |
| qt_h125 | Hot | 54 °C (isothermal) | 5 324.7 | Distillation condenser |
| qt_h126 | Cold | 67 °C (isothermal) | 5 643.5 | Distillation reboiler |
| qt_h127 | Hot | 30 °C (isothermal) | 12.5 | Auxiliary preflash cooler |
| qt_h128 | Hot | 54 °C → 25 °C | 344.7 | Condenser-effluent subcooling |
| qt_h129 | Hot | 67 °C → 25 °C | 2.65 | Bottoms-effluent subcooling |
| qt_h130 | Hot | 1 000 °C (isothermal) | 3 634 | Purge-gas flaring (stage 1) |
| qt_h131 | Hot | 1 000 °C → 150 °C | 2 190 | Purge-gas flaring (stage 2) |

The reactor isothermal cooling (qt_h124, **10.7 MW at 210 °C**) and the flaring at 1 000 °C (qt_h130–131, **5.8 MW combined**) are the dominant high-grade thermal exports of the plant; matching them against suitable demands (e.g. the distillation reboiler, or a steam generator) is where most of the heat-integration value of the plant lies.

## 7. Equipment and cost

The plant comprises (per the model's equipment list):

| Equipment | Subtype |
|:----------|:--------|
| Syngas compressor — stage 1 | Centrifugal |
| Syngas compressor — stage 2 | Centrifugal |
| Methanol reactor | Fixed-bed catalytic |
| Distillation column | Tray column |
| MeOH plant (composite) | – |

Capital cost is taken as a **size-scaled correlation** in the methanol energy output, anchored on a 30.2 MW reference plant costing 18.3 M EUR (2022 EUR):

$$C_{inv2,MeOH} \;=\; C_{base}\,\left(\dfrac{\dot Q_{MeOH}}{\dot Q_{base}}\right)^{sc}\,\dfrac{i(1+i)^{n}}{(1+i)^{n}-1}, \qquad C_{base}=18.3\ \mathrm{M\,EUR},\;\dot Q_{base}=30.2\ \mathrm{MW},\;sc=0.8.$$

| Item | Value |
|:-----|:------|
| Lifetime | 40 years |
| Interest rate | 0.06 |
| Reference plant CAPEX (basis 2022) | 18.3 M EUR |
| Reference plant capacity (basis) | 30.2 MW (methanol LHV) |
| Scaling exponent | 0.8 |
| Capacity range | 0 × to 100 × reference |
| Fixed operating cost | 0 EUR/y |
| Variable operating cost | 0 EUR/h |

Operating costs are zero in the reference model — feedstock (syngas), utility (electricity), product (methanol), and emission (CO₂) flows enter the optimisation through the resource interfaces of §6.

## 8. References

1. Domingos, M. E. G. R. *et al.* *Techno-economic and environmental analysis of methanol and dimethyl ether production from syngas in a kraft pulp process.* <https://www.sciencedirect.com/science/article/pii/S009813542200148X>.
2. Tountas, A. A. *et al.* (2019). *Towards solar methanol: past, present, and future.* **Advanced Science** **6** (8), 1801903.
3. Kiss, A. A., Pragt, J., Vos, H., Bargeman, G. & De Groot, M. (2016). *Novel efficient process for methanol synthesis by CO₂ hydrogenation.* **Chemical Engineering Journal** **284**, 260–269.
4. *Journal of CO₂ Utilization* (2023). DOI: <https://doi.org/10.1016/j.jcou.2023.102563>.

## 9. Cite as

> Flórez-Orrego, D. & Domingos, M. *Methanol Production — Ex-ante energy-technology model (ET, v1).* IEA IETS Task XXIV / Subtask 1, Activity 3.1. EPFL IPESE, Lausanne, 2025. Contact: <daniel.florezorrego@epfl.ch>.
