## Rigorous source base for emergence-first planning (VMT Phase 2.5 → 3)

- Scope: small-N exchange (2 goods, 2 agents) for theory; ABM remains spatial bilateral trade. Architecture constraint: Protocol → Effect → State; theory calculators do not mutate ABM state. UI emphasis: visual-first, progressive disclosure; Edgeworth Box is the bridge to bargaining.
- Deliverable format: consolidated planning-only research file with the following sections embedded.

### 01_annotated_bibliography

#### Neoclassical theory: GE, tâtonnement, stability, gross substitutes, counterexamples
- Jehle, Geoffrey A., and Philip J. Reny (2011). Advanced Microeconomic Theory (3rd ed.). Pearson.
  - DOI/URL: publisher; library link preferred.
  - Sections/pages: Consumer theory (Ch. 1–3), Duality and Slutsky (Ch. 4), General equilibrium and welfare (Ch. 5). Page ranges vary by edition.
  - Relevance: Canonical graduate-level reference for consumer/duality, GE, and welfare. Good for clearly stated assumptions and theorems used by calculators.
  - BibTeX: see sources.bib (jehle2011advanced).

- Mas-Colell, Andreu, Michael D. Whinston, and Jerry R. Green (1995). Microeconomic Theory. Oxford University Press.
  - URL: publisher; widely held.
  - Sections/pages: Consumer (Ch. 2–3), Demand/Duality/Slutsky (Ch. 3, 4, 8), Exchange economies and GE (Ch. 15–17), Welfare (Ch. 16), Existence/Stability (Ch. 17). Page ranges vary by printing.
  - Relevance: MWG remains the standard for exchange economies, excess demand, and welfare theorems; precise Slutsky and duality definitions.
  - BibTeX: mascolell1995microeconomic.

- Arrow, Kenneth J., and Leonid Hurwicz (1958). On the Stability of the Competitive Equilibrium, I. Econometrica 26(4): 522–552.
  - URL: `https://www.econometricsociety.org/publications/econometrica/1958/10/01/stability-competitive-equilibrium-i`
  - Pages: 522–552.
  - Relevance: Classical tâtonnement stability analysis; conditions implying local/global stability, including gross substitutes-type restrictions.
  - BibTeX: arrow1958stability.

- Arrow, Kenneth J., Theodore E. O. Block, and Leonid Hurwicz (1959). On the Stability of the Competitive Equilibrium, II. Econometrica 27(1): 82–109.
  - URL: `https://www.econometricsociety.org/publications/econometrica/1959/01/01/stability-competitive-equilibrium-ii`
  - Pages: 82–109.
  - Relevance: Continuation to I; further convergence and stability results.
  - BibTeX: arrow1959stabilityii.

- Smale, Stephen (1976). A Convergent Process of Price Adjustment and Global Newton Methods. Journal of Mathematical Economics 3(2): 107–120.
  - DOI: `https://doi.org/10.1016/0304-4068(76)90010-1`
  - Pages: 107–120.
  - Relevance: Global Newton-style price adjustment; numerical underpinning for robust solvers beyond naïve tâtonnement.
  - BibTeX: smale1976convergent.

- Scarf, Herbert (1960). Some Examples of Global Instability of the Competitive Equilibrium. International Economic Review 1(3): 157–172.
  - Stable URL: `https://www.jstor.org/stable/2525408`
  - Pages: 157–172.
  - Relevance: Classic counterexamples to tâtonnement stability; motivates honest caveats and pedagogy around failure modes.
  - BibTeX: scarf1960instability.

- Gul, Faruk, and Ennio Stacchetti (1999). Walrasian Equilibrium with Gross Substitutes. Journal of Economic Theory 87(1): 95–124.
  - DOI: `https://doi.org/10.1006/jeth.1999.2550`
  - Pages: 95–124.
  - Relevance: Gross substitutes structure implies existence/uniqueness and monotone comparative statics; central to positive convergence results.
  - BibTeX: gul1999gross.

- Kelso, Alexander S., Jr., and Vincent P. Crawford (1982). Job Matching, Coalition Formation, and Gross Substitutes. Econometrica 50(6): 1483–1504.
  - Stable URL: `https://www.jstor.org/stable/1913392`
  - Pages: 1483–1504.
  - Relevance: Gross substitutes in discrete assignment/matching; links to convergence and lattice structure of equilibria.
  - BibTeX: kelso1982gross.

- Sonnenschein (1972, 1973), Mantel (1974), Debreu (1974) SMD results.
  - URLs: journal pages (SMD trio); see BibTeX entries.
  - Relevance: General excess demand can approximate any continuous function satisfying Walras’ law; limits predictive power of tâtonnement/convergence claims outside special classes.
  - BibTeX: sonnenschein1972, sonnenschein1973, mantel1974, debreu1974smd.

#### Edgeworth Box foundations; contract curve; core vs competitive; pedagogy
- Edgeworth, Francis Y. (1881). Mathematical Psychics. Kegan Paul.
  - URL: `https://archive.org/details/mathematicalpsych00edgeuoft`
  - Pages: Ch. II–III (exchange; contract curve).
  - Relevance: Origin of the Edgeworth Box; contract curve and core.
  - BibTeX: edgeworth1881.

- Varian, Hal R. (1992). Microeconomic Analysis (3rd ed.). W.W. Norton.
  - Sections/pages: Exchange economies, Pareto sets, core vs competitive (Ch. 17). Pages vary by printing.
  - Relevance: Clean formal derivations for 2×2 exchange pedagogy and connection to competitive equilibria.
  - BibTeX: varian1992micro.

- Debreu, Gérard (1959). Theory of Value. Yale University Press.
  - Pages: Ch. 4–6.
  - Relevance: Core–equilibrium links in finite economies; existence.
  - BibTeX: debreu1959value.

- Acemoglu, Daron (2009). Exchange Economies and Equilibria (MIT 14.121 Lecture Notes).
  - PDF: `https://economics.mit.edu/files/4153`
  - Pages: see Sections 1–2; contract curve, core, welfare theorems.
  - Relevance: Clear graduate notes for 2×2 exchange and Edgeworth Box pedagogy.
  - BibTeX: acemoglu2009exchange.

- Levin, Jonathan (Stanford Econ 202) General Equilibrium notes.
  - PDF: `https://web.stanford.edu/~jdlevin/Econ%20202/General%20Equilibrium.pdf`
  - Pages: early sections on exchange and welfare.
  - Relevance: Concise GE derivations; good figures for pedagogy.
  - BibTeX: levinGE.

#### Bargaining theory; links to Edgeworth feasible set
- Nash, John F. (1950). The Bargaining Problem. Econometrica 18(2): 155–162.
  - Stable URL: `https://www.jstor.org/stable/1907266`
  - Relevance: Axioms and closed-form solution for the two-person bargaining problem; used for feasible set in Edgeworth Box.
  - BibTeX: nash1950.

- Kalai, Ehud, and Meir Smorodinsky (1975). Other Solutions to Nash's Bargaining Problem. Econometrica 43(3): 513–518.
  - Stable URL: `https://www.jstor.org/stable/1914280`
  - Relevance: Proportional gains solution; monotonicity axiom; useful for alternative UI pedagogy.
  - BibTeX: kalai1975.

- Rubinstein, Ariel (1982). Perfect Equilibrium in a Bargaining Model. Econometrica 50(1): 97–109.
  - Stable URL: `https://www.jstor.org/stable/1912531`
  - Relevance: Alternating-offers model with discounting; dynamic foundation for Nash under limits.
  - BibTeX: rubinstein1982.

- Osborne, Martin J., and Ariel Rubinstein (1990). Bargaining and Markets. Academic Press.
  - URL: publisher.
  - Relevance: Comprehensive treatment; connects bargaining to market contexts.
  - BibTeX: osborneRubinstein1990.

- Osborne, Martin J., and Ariel Rubinstein (1994). A Course in Game Theory. MIT Press. Free PDF: `https://www.economics.utoronto.ca/osborne/igt/igt.pdf`
  - Relevance: Ch. 16–17 (bargaining) give crisp derivations and proofs suitable for implementation notes.
  - BibTeX: osborneRubinstein1994.

#### Matching/search for decentralized exchange; thin vs thick; spatial search
- Gale, David, and Lloyd S. Shapley (1962). College Admissions and the Stability of Marriage. American Mathematical Monthly 69(1): 9–15.
  - DOI: `https://doi.org/10.2307/2312726`
  - Relevance: Stable matching algorithm; foundational for decentralized pairing mechanisms.
  - BibTeX: gale1962.

- Burdett, Kenneth, and Kenneth L. Judd (1983). Equilibrium Price Dispersion. Econometrica 51(4): 955–969.
  - Stable URL: `https://www.jstor.org/stable/1912660`
  - Relevance: Search with endogenous price dispersion; thin vs thick market implications.
  - BibTeX: burdett1983.

- Diamond, Peter A. (1971). A Model of Price Adjustment. Journal of Economic Theory 3(2): 156–168.
  - DOI: `https://doi.org/10.1016/0022-0531(71)90066-8`
  - Relevance: Search frictions and price adjustment; benchmark for decentralized trade frictions.
  - BibTeX: diamond1971.

#### ABM/ACE; market formation; price convergence; institutions
- Tesfatsion, Leigh, and Kenneth L. Judd (eds.) (2006). Handbook of Computational Economics vol. 2: Agent-Based Computational Economics. Elsevier.
  - URL: `https://www.sciencedirect.com/handbook/handbook-of-computational-economics/vol/2`
  - Relevance: Canonical ACE overview; includes market formation and convergence content.
  - BibTeX: tesfatsion2006.

- LeBaron, Blake (2006). Agent-Based Computational Finance. In Tesfatsion & Judd (eds.), Handbook of Computational Economics vol. 2, Ch. 24.
  - URL: publisher chapter page.
  - Relevance: Institutional baselines and convergence patterns in decentralized trading.
  - BibTeX: lebaron2006.

- Gode, Dhananjay K., and Shyam Sunder (1993). Allocative Efficiency of Markets with Zero-Intelligence Traders. Journal of Political Economy 101(1): 119–137.
  - DOI: `https://doi.org/10.1086/261868`
  - Relevance: Institution-driven efficiency baseline; useful comparator for ABM market mechanisms.
  - BibTeX: gode1993.

- Smith, Vernon L. (1962). An Experimental Study of Competitive Market Behavior. Journal of Political Economy 70(2): 111–137.
  - DOI: `https://doi.org/10.1086/258636`
  - Relevance: Double auction convergence and price discovery; empirical foundation for decentralized price formation.
  - BibTeX: smith1962.

- Plott, Charles R., and Shyam Sunder (1982). Rational Expectations and the Aggregation of Diverse Information in Laboratory Security Markets. Econometrica 50(5): 1085–1118.
  - Stable URL: `https://www.jstor.org/stable/1911866`
  - Relevance: Information aggregation and price convergence in decentralized markets.
  - BibTeX: plott1982.

- Menkveld, Albert J. (2023). The Economics of High-Frequency Trading. Annual Review of Financial Economics 15: 53–72.
  - DOI: `https://doi.org/10.1146/annurev-financial-110122-104830`
  - Relevance: Modern survey on microstructure and information; useful for information-flow and price-convergence pedagogy.
  - BibTeX: menkveld2023.

#### Market information & coordination mechanisms (VWAP-like aggregation; broadcasting)
- Bertsimas, Dimitris, and Andrew W. Lo (1998). Optimal Control of Execution Costs. Journal of Financial Markets 1(1): 1–50.
  - DOI: `https://doi.org/10.1016/S1386-4181(97)00002-4`
  - Relevance: VWAP/TWAP execution and averaging schemes; connects to aggregation signals design.
  - BibTeX: bertsimas1998.

- Almgren, Robert, and Neil Chriss (2000). Optimal Execution of Portfolio Transactions. Journal of Risk 3(2): 5–40.
  - URL: publisher (widely available preprints).
  - Relevance: Execution under information and impact; aggregation windows and stability considerations.
  - BibTeX: almgren2000.

- Madhavan, Ananth (1992). Trading Mechanisms in Securities Markets. Journal of Finance 47(2): 607–641.
  - DOI: `https://doi.org/10.1111/j.1540-6261.1992.tb04406.x`
  - Relevance: Mechanism design and information aggregation via market rules; implications for simple broadcast signals.
  - BibTeX: madhavan1992.

#### Money emergence
- Kiyotaki, Nobuhiro, and Randall Wright (1989). On Money as a Medium of Exchange. Journal of Political Economy 97(4): 927–954.
  - DOI: `https://doi.org/10.1086/261634`
  - Relevance: Search-theoretic money; conditions for commodity-money emergence; informs “money-like” good diagnostics.
  - BibTeX: kiyotaki1989.

- Lagos, Ricardo, and Randall Wright (2005). A Unified Framework for Monetary Theory and Policy Analysis. Journal of Political Economy 113(3): 463–484.
  - DOI: `https://doi.org/10.1086/429804`
  - Relevance: LW model for tractable frictions; bridges search money with policy/aggregation; reference for emergent medium of exchange.
  - BibTeX: lagos2005.

- Ostroy, Joseph, and Ross M. Starr (1990). The Transactions Role of Money. In Handbook of Monetary Economics vol. 1, pp. 3–62.
  - URL: publisher (Elsevier/ScienceDirect).
  - Relevance: Classic survey on money as coordination device; connects to decentralization and information.
  - BibTeX: ostroy1990.

#### Numerical methods and 2×2 calculators
- Scarf, Herbert E., with Terje Hansen (1973). The Computation of Economic Equilibria. Yale University Press.
  - Relevance: Pivoting algorithms and fixed-point computations; small-scale GE computation foundations.
  - BibTeX: scarf1973book.

- Shoven, John B., and John Whalley (1992). Applying General Equilibrium. Cambridge University Press.
  - Relevance: Practical GE algorithms and calibration; small-dimension cases and numerical pitfalls.
  - BibTeX: shoven1992.

- Judd, Kenneth L. (1998). Numerical Methods in Economics. MIT Press.
  - DOI: `https://doi.org/10.7551/mitpress/7284.001.0001`
  - Relevance: Robust root-finding, fixed-point, stability diagnostics; practical tips for 2×2 solvers.
  - BibTeX: judd1998.

- Varian, Hal R. (1992). Microeconomic Analysis (3rd ed.).
  - Sections: Cobb–Douglas and CES closed-form demand/expenditure; Slutsky matrix.
  - Relevance: Closed forms for 2-good demands; validates calculator formulas.
  - BibTeX: varian1992micro.

- Graduate lecture notes on Edgeworth contract curve and CE computation.
  - Examples: Acemoglu (MIT) and Levin (Stanford) notes above.

#### Pedagogical/UX for micro visualization
- Osborne & Rubinstein (1994). A Course in Game Theory. Free PDF.
  - Relevance: Clean figures and stepwise derivations; good for progressive disclosure in bargaining UI.

- Levin (GE notes) and Acemoglu (Exchange) PDFs.
  - Relevance: Concise figures/derivations; helpful for Edgeworth Box visuals and core vs competitive overlays.


### 02_topic_to_source_map

| Plan topic | Primary sources | Algorithms / proofs | Lecture notes (PDF) | Risks / limitations |
|---|---|---|---|---|
| Consumer Theory Lab (2 goods) | MWG (Ch. 2–4), Jehle & Reny (Ch. 1–4), Varian (Ch. 8, 17) | Slutsky decomposition; duality (expenditure, indirect utility); Shephard’s lemma | Varian-style notes; Acemoglu exchange intro | Corner solutions; non-homothetic preferences; numerical instability at kinks |
| Edgeworth + Bargaining (2×2) | Edgeworth (1881), Varian (Ch. 17), Debreu (1959) | Contract curve derivation; Core ⊇ CE; 1st/2nd welfare theorems | Levin GE notes; Acemoglu Exchange | Core ≠ CE in small markets; multiple equilibria; endowment sensitivity |
| Bargaining (Nash/Kalai/Rubinstein) | Nash (1950), Kalai–Smorodinsky (1975), Rubinstein (1982), Osborne–Rubinstein (1994) | Nash axioms; KS monotonicity; alternating-offers closed form | Osborne–Rubinstein textbook PDF | Disagreement point choice; dynamic inconsistency under changing discounting |
| Tâtonnement GE (2×2) | Arrow–Hurwicz (1958, 1959), Smale (1976), Gul–Stacchetti (1999), Scarf (1960) | Stability conditions; global Newton; gross substitutes uniqueness; Scarf counterexamples | Levin GE notes | SMD pathologies; global cycles; step-size sensitivity; non-convergence |
| Producer basics (for later) | MWG (Ch. 5–6, 18), Shoven–Whalley (1992), Judd (1998) | Cost minimization; duality; GE with firms | Standard micro notes | Non-convexities; increasing returns; multiplicity |


### 03_solver_refs

- Marshallian demand (2 goods)
  - Method: Closed forms for Cobb–Douglas; for CES use FOCs; general case via root-finding on FOCs with budget.
  - Assumptions: Strictly convex, monotone preferences; interior solutions for closed forms.
  - Caveats: Handle corners; normalize prices to reduce ill-conditioning; scale goods if magnitudes differ.
  - References: Varian (Ch. on demand/duality); MWG (Ch. 3–4); Jehle & Reny (Ch. 2–4).
  - Tips: Use log-utility for Cobb–Douglas to avoid underflow; validate homogeneity of degree zero.

- Hicksian demand and expenditure function (2 goods)
  - Method: Minimize expenditure s.t. utility constraint; use Lagrangian → Hicksian demands; apply Shephard’s lemma.
  - Assumptions: u is continuous, strictly quasi-concave.
  - Caveats: Numerical issues near indifference curvature extremes; check Slutsky symmetry.
  - References: MWG (dual), Jehle & Reny (duality), Varian.
  - Tips: Implement both primal and dual to cross-check indirect utility and expenditure.

- Slutsky matrix
  - Method: Compute Marshallian demands; differentiate w.r.t. prices/income; or assemble via Hicksian + Shephard’s lemma.
  - Assumptions: Differentiability.
  - Caveats: Numerical derivatives are noisy; prefer analytic forms for common classes (CD, CES).
  - References: MWG, Varian, Jehle & Reny.
  - Tips: Enforce symmetry and negative semi-definiteness checks as diagnostics.

- Edgeworth contract curve (2×2)
  - Method: Set MRS_A(p_A) = MRS_B(p_B) along feasible set; solve with endowment constraint; for CD/CES closed forms exist.
  - Assumptions: Differentiable, strictly convex preferences.
  - Caveats: Indifference tangencies fail at corners; handle kinks.
  - References: Varian (Ch. 17), Acemoglu/Levin notes.
  - Tips: Solve in shares; parameterize by one good’s share to avoid degeneracy.

- 2×2 competitive equilibrium (exchange)
  - Method: Excess demand z(p)=0 with price normalization; for CD, closed-form; else 1D root on relative price.
  - Assumptions: Standard GE assumptions; gross substitutes yields uniqueness.
  - Caveats: Tâtonnement may cycle; root-finding needs bracketing and monotonicity checks.
  - References: Arrow–Hurwicz (stability), Gul–Stacchetti (GS), Scarf (counterexamples), Smale (Newton).
  - Tips: Use bisection+secant hybrid on relative price; check Walras’ law to validate residuals.

- Nash bargaining (2 goods feasible set)
  - Method: Maximize (u_A - d_A)(u_B - d_B) over feasible utility frontier; for CD utilities closed forms exist.
  - Assumptions: Convex, compact feasible set; non-empty individually rational set.
  - Caveats: Disagreement point sensitivity; numerical trace along Pareto frontier.
  - References: Nash (1950); Osborne–Rubinstein (1994).
  - Tips: Precompute Pareto frontier via contract-curve tracing; then 1D search in utility space.

- Kalai–Smorodinsky bargaining
  - Method: Choose Pareto point that preserves proportional gains to utopia; solve intersection with Pareto frontier.
  - Assumptions: As above; need utopia/best utilities.
  - Caveats: Non-unique utopia under non-convexities; sensitivity to scaling.
  - References: Kalai–Smorodinsky (1975).
  - Tips: Normalize utilities; compute utopia via separate unconstrained maximization for each agent.

- Rubinstein alternating offers
  - Method: Closed-form stationary equilibrium with discount factors δ_A, δ_B.
  - Assumptions: Infinite horizon, common knowledge δ∈(0,1).
  - Caveats: Time discretization for UI; link to Nash as δ→1.
  - References: Rubinstein (1982); Osborne–Rubinstein (1994).
  - Tips: Provide UI slider for discounting; show limit to Nash visually.


### 04_conflicts_and_resolutions (emergence-first vs centralized demos)

- Conflict: Centralized tâtonnement implies an auctioneer; emergence-first emphasizes bilateral trade.
  - Resolution: Frame tâtonnement as benchmark “planner shadow process” to compare against ABM bilateral outcomes; show where it fails (Scarf, SMD) and where it works (gross substitutes). Provide an “institution-neutral” price signal (e.g., VWAP-like rolling quote) derived from bilateral trades.

- Conflict: GE solvers directly set prices/allocations; emergence-first wants decentralized convergence.
  - Resolution: Use GE solutions as “targets/bounds” overlays on Edgeworth Box; ABM trajectories are drawn in allocation space. Emphasize “compare-to-ABM” rather than “replace ABM”.

- Conflict: Stability demos can mislead when pathologies exist.
  - Resolution: Teach with counterexamples: include Scarf cycles; show step-size dependence; present GS cases with convergence proofs alongside SMD caveats. Use Smale/Newton variants with safeguards.

- Conflict: Broadcasting VWAP may feel centralized.
  - Resolution: Treat VWAP as emergent information aggregation from bilateral trades published locally; implement as rolling, local (windowed) average with lag; compare convergence speeds vs no-broadcast baseline.


### sources.bib

```bibtex
@book{jehle2011advanced,
  title={Advanced Microeconomic Theory},
  author={Jehle, Geoffrey A. and Reny, Philip J.},
  edition={3rd},
  year={2011},
  publisher={Pearson}
}

@book{mascolell1995microeconomic,
  title={Microeconomic Theory},
  author={Mas-Colell, Andreu and Whinston, Michael D. and Green, Jerry R.},
  year={1995},
  publisher={Oxford University Press}
}

@article{arrow1958stability,
  title={On the Stability of the Competitive Equilibrium, I},
  author={Arrow, Kenneth J. and Hurwicz, Leonid},
  journal={Econometrica},
  volume={26},
  number={4},
  pages={522--552},
  year={1958},
  url={https://www.econometricsociety.org/publications/econometrica/1958/10/01/stability-competitive-equilibrium-i}
}

@article{arrow1959stabilityii,
  title={On the Stability of the Competitive Equilibrium, II},
  author={Arrow, Kenneth J. and Block, Theodore E. O. and Hurwicz, Leonid},
  journal={Econometrica},
  volume={27},
  number={1},
  pages={82--109},
  year={1959},
  url={https://www.econometricsociety.org/publications/econometrica/1959/01/01/stability-competitive-equilibrium-ii}
}

@article{smale1976convergent,
  title={A Convergent Process of Price Adjustment and Global Newton Methods},
  author={Smale, Stephen},
  journal={Journal of Mathematical Economics},
  volume={3},
  number={2},
  pages={107--120},
  year={1976},
  doi={10.1016/0304-4068(76)90010-1}
}

@article{scarf1960instability,
  title={Some Examples of Global Instability of the Competitive Equilibrium},
  author={Scarf, Herbert},
  journal={International Economic Review},
  volume={1},
  number={3},
  pages={157--172},
  year={1960},
  url={https://www.jstor.org/stable/2525408}
}

@article{gul1999gross,
  title={Walrasian Equilibrium with Gross Substitutes},
  author={Gul, Faruk and Stacchetti, Ennio},
  journal={Journal of Economic Theory},
  volume={87},
  number={1},
  pages={95--124},
  year={1999},
  doi={10.1006/jeth.1999.2550}
}

@article{kelso1982gross,
  title={Job Matching, Coalition Formation, and Gross Substitutes},
  author={Kelso, Alexander S. and Crawford, Vincent P.},
  journal={Econometrica},
  volume={50},
  number={6},
  pages={1483--1504},
  year={1982},
  url={https://www.jstor.org/stable/1913392}
}

@article{sonnenschein1972,
  title={Market Excess Demand Functions},
  author={Sonnenschein, Hugo},
  journal={Econometrica},
  volume={40},
  number={3},
  pages={549--563},
  year={1972}
}

@article{sonnenschein1973,
  title={Do Walras' Identity and Continuity Characterize the Class of Community Excess Demand Functions?},
  author={Sonnenschein, Hugo},
  journal={Journal of Economic Theory},
  volume={6},
  number={4},
  pages={345--354},
  year={1973}
}

@article{mantel1974,
  title={On the Characterization of Aggregate Excess Demand},
  author={Mantel, R.},
  journal={Journal of Economic Theory},
  volume={7},
  number={3},
  pages={348--353},
  year={1974}
}

@article{debreu1974smd,
  title={Excess Demand Functions},
  author={Debreu, G{\'e}rard},
  journal={Journal of Mathematical Economics},
  volume={1},
  number={1},
  pages={15--23},
  year={1974}
}

@book{edgeworth1881,
  title={Mathematical Psychics},
  author={Edgeworth, Francis Y.},
  year={1881},
  publisher={Kegan Paul},
  url={https://archive.org/details/mathematicalpsych00edgeuoft}
}

@book{varian1992micro,
  title={Microeconomic Analysis},
  author={Varian, Hal R.},
  edition={3rd},
  year={1992},
  publisher={W.W. Norton}
}

@book{debreu1959value,
  title={Theory of Value: An Axiomatic Analysis of Economic Equilibrium},
  author={Debreu, G{\'e}rard},
  year={1959},
  publisher={Yale University Press}
}

@misc{acemoglu2009exchange,
  title={Exchange Economies and Equilibria},
  author={Acemoglu, Daron},
  year={2009},
  howpublished={MIT 14.121 Lecture Notes},
  url={https://economics.mit.edu/files/4153}
}

@misc{levinGE,
  title={General Equilibrium},
  author={Levin, Jonathan},n  howpublished={Stanford Econ 202 Notes},
  url={https://web.stanford.edu/~jdlevin/Econ%20202/General%20Equilibrium.pdf}
}

@article{nash1950,
  title={The Bargaining Problem},
  author={Nash, John F.},
  journal={Econometrica},
  volume={18},
  number={2},
  pages={155--162},
  year={1950},
  url={https://www.jstor.org/stable/1907266}
}

@article{kalai1975,
  title={Other Solutions to Nash's Bargaining Problem},
  author={Kalai, Ehud and Smorodinsky, Meir},
  journal={Econometrica},
  volume={43},
  number={3},
  pages={513--518},
  year={1975},
  url={https://www.jstor.org/stable/1914280}
}

@article{rubinstein1982,
  title={Perfect Equilibrium in a Bargaining Model},
  author={Rubinstein, Ariel},
  journal={Econometrica},
  volume={50},
  number={1},
  pages={97--109},
  year={1982},
  url={https://www.jstor.org/stable/1912531}
}

@book{osborneRubinstein1990,
  title={Bargaining and Markets},
  author={Osborne, Martin J. and Rubinstein, Ariel},
  year={1990},
  publisher={Academic Press}
}

@book{osborneRubinstein1994,
  title={A Course in Game Theory},
  author={Osborne, Martin J. and Rubinstein, Ariel},
  year={1994},
  publisher={MIT Press},
  url={https://www.economics.utoronto.ca/osborne/igt/igt.pdf}
}

@article{gale1962,
  title={College Admissions and the Stability of Marriage},
  author={Gale, David and Shapley, Lloyd S.},
  journal={American Mathematical Monthly},
  volume={69},
  number={1},
  pages={9--15},
  year={1962},
  doi={10.2307/2312726}
}

@article{burdett1983,
  title={Equilibrium Price Dispersion},
  author={Burdett, Kenneth and Judd, Kenneth L.},
  journal={Econometrica},
  volume={51},
  number={4},
  pages={955--969},
  year={1983},
  url={https://www.jstor.org/stable/1912660}
}

@article{diamond1971,
  title={A Model of Price Adjustment},
  author={Diamond, Peter A.},
  journal={Journal of Economic Theory},
  volume={3},
  number={2},
  pages={156--168},
  year={1971},
  doi={10.1016/0022-0531(71)90066-8}
}

@book{tesfatsion2006,
  title={Handbook of Computational Economics: Agent-Based Computational Economics},
  editor={Tesfatsion, Leigh and Judd, Kenneth L.},
  volume={2},
  year={2006},
  publisher={Elsevier}
}

@incollection{lebaron2006,
  title={Agent-Based Computational Finance},
  author={LeBaron, Blake},
  booktitle={Handbook of Computational Economics, Vol. 2},
  editor={Tesfatsion, Leigh and Judd, Kenneth L.},
  year={2006},
  publisher={Elsevier}
}

@article{gode1993,
  title={Allocative Efficiency of Markets with Zero-Intelligence Traders},
  author={Gode, Dhananjay K. and Sunder, Shyam},
  journal={Journal of Political Economy},
  volume={101},
  number={1},
  pages={119--137},
  year={1993},
  doi={10.1086/261868}
}

@article{smith1962,
  title={An Experimental Study of Competitive Market Behavior},
  author={Smith, Vernon L.},
  journal={Journal of Political Economy},
  volume={70},
  number={2},
  pages={111--137},
  year={1962},
  doi={10.1086/258636}
}

@article{plott1982,
  title={Rational Expectations and the Aggregation of Diverse Information in Laboratory Security Markets},
  author={Plott, Charles R. and Sunder, Shyam},
  journal={Econometrica},
  volume={50},
  number={5},
  pages={1085--1118},
  year={1982},
  url={https://www.jstor.org/stable/1911866}
}

@article{menkveld2023,
  title={The Economics of High-Frequency Trading},
  author={Menkveld, Albert J.},
  journal={Annual Review of Financial Economics},
  volume={15},
  pages={53--72},
  year={2023},
  doi={10.1146/annurev-financial-110122-104830}
}

@article{bertsimas1998,
  title={Optimal Control of Execution Costs},
  author={Bertsimas, Dimitris and Lo, Andrew W.},
  journal={Journal of Financial Markets},
  volume={1},
  number={1},
  pages={1--50},
  year={1998},
  doi={10.1016/S1386-4181(97)00002-4}
}

@article{almgren2000,
  title={Optimal Execution of Portfolio Transactions},
  author={Almgren, Robert and Chriss, Neil},
  journal={Journal of Risk},
  volume={3},
  number={2},
  pages={5--40},
  year={2000}
}

@article{madhavan1992,
  title={Trading Mechanisms in Securities Markets},
  author={Madhavan, Ananth},
  journal={The Journal of Finance},
  volume={47},
  number={2},
  pages={607--641},
  year={1992},
  doi={10.1111/j.1540-6261.1992.tb04406.x}
}

@article{kiyotaki1989,
  title={On Money as a Medium of Exchange},
  author={Kiyotaki, Nobuhiro and Wright, Randall},
  journal={Journal of Political Economy},
  volume={97},
  number={4},
  pages={927--954},
  year={1989},
  doi={10.1086/261634}
}

@article{lagos2005,
  title={A Unified Framework for Monetary Theory and Policy Analysis},
  author={Lagos, Ricardo and Wright, Randall},
  journal={Journal of Political Economy},
  volume={113},
  number={3},
  pages={463--484},
  year={2005},
  doi={10.1086/429804}
}

@incollection{ostroy1990,
  title={The Transactions Role of Money},
  author={Ostroy, Joseph and Starr, Ross M.},
  booktitle={Handbook of Monetary Economics},
  volume={1},
  pages={3--62},
  year={1990},
  publisher={Elsevier}
}

@book{scarf1973book,
  title={The Computation of Economic Equilibria},
  author={Scarf, Herbert E. and Hansen, Terje},
  year={1973},
  publisher={Yale University Press}
}

@book{shoven1992,
  title={Applying General Equilibrium},
  author={Shoven, John B. and Whalley, John},
  year={1992},
  publisher={Cambridge University Press}
}

@book{judd1998,
  title={Numerical Methods in Economics},
  author={Judd, Kenneth L.},
  year={1998},
  publisher={MIT Press},
  doi={10.7551/mitpress/7284.001.0001}
}
```


### links.json

```json
{
  "arrow1958stability": {
    "url": "https://www.econometricsociety.org/publications/econometrica/1958/10/01/stability-competitive-equilibrium-i",
    "wayback": "https://web.archive.org/web/*/https://www.econometricsociety.org/publications/econometrica/1958/10/01/stability-competitive-equilibrium-i"
  },
  "arrow1959stabilityii": {
    "url": "https://www.econometricsociety.org/publications/econometrica/1959/01/01/stability-competitive-equilibrium-ii",
    "wayback": "https://web.archive.org/web/*/https://www.econometricsociety.org/publications/econometrica/1959/01/01/stability-competitive-equilibrium-ii"
  },
  "scarf1960instability": {
    "url": "https://www.jstor.org/stable/2525408",
    "wayback": "https://web.archive.org/web/*/https://www.jstor.org/stable/2525408"
  },
  "gul1999gross": {
    "url": "https://doi.org/10.1006/jeth.1999.2550",
    "wayback": "https://web.archive.org/web/*/https://doi.org/10.1006/jeth.1999.2550"
  },
  "kelso1982gross": {
    "url": "https://www.jstor.org/stable/1913392",
    "wayback": "https://web.archive.org/web/*/https://www.jstor.org/stable/1913392"
  },
  "nash1950": {
    "url": "https://www.jstor.org/stable/1907266",
    "wayback": "https://web.archive.org/web/*/https://www.jstor.org/stable/1907266"
  },
  "kalai1975": {
    "url": "https://www.jstor.org/stable/1914280",
    "wayback": "https://web.archive.org/web/*/https://www.jstor.org/stable/1914280"
  },
  "rubinstein1982": {
    "url": "https://www.jstor.org/stable/1912531",
    "wayback": "https://web.archive.org/web/*/https://www.jstor.org/stable/1912531"
  },
  "gale1962": {
    "url": "https://doi.org/10.2307/2312726",
    "wayback": "https://web.archive.org/web/*/https://doi.org/10.2307/2312726"
  },
  "burdett1983": {
    "url": "https://www.jstor.org/stable/1912660",
    "wayback": "https://web.archive.org/web/*/https://www.jstor.org/stable/1912660"
  },
  "gode1993": {
    "url": "https://doi.org/10.1086/261868",
    "wayback": "https://web.archive.org/web/*/https://doi.org/10.1086/261868"
  },
  "smith1962": {
    "url": "https://doi.org/10.1086/258636",
    "wayback": "https://web.archive.org/web/*/https://doi.org/10.1086/258636"
  },
  "plott1982": {
    "url": "https://www.jstor.org/stable/1911866",
    "wayback": "https://web.archive.org/web/*/https://www.jstor.org/stable/1911866"
  },
  "menkveld2023": {
    "url": "https://doi.org/10.1146/annurev-financial-110122-104830",
    "wayback": "https://web.archive.org/web/*/https://doi.org/10.1146/annurev-financial-110122-104830"
  },
  "bertsimas1998": {
    "url": "https://doi.org/10.1016/S1386-4181(97)00002-4",
    "wayback": "https://web.archive.org/web/*/https://doi.org/10.1016/S1386-4181(97)00002-4"
  },
  "almgren2000": {
    "url": "https://risk.net",
    "wayback": "https://web.archive.org/web/*/https://risk.net"
  },
  "madhavan1992": {
    "url": "https://doi.org/10.1111/j.1540-6261.1992.tb04406.x",
    "wayback": "https://web.archive.org/web/*/https://doi.org/10.1111/j.1540-6261.1992.tb04406.x"
  },
  "kiyotaki1989": {
    "url": "https://doi.org/10.1086/261634",
    "wayback": "https://web.archive.org/web/*/https://doi.org/10.1086/261634"
  },
  "lagos2005": {
    "url": "https://doi.org/10.1086/429804",
    "wayback": "https://web.archive.org/web/*/https://doi.org/10.1086/429804"
  },
  "edgeworth1881": {
    "url": "https://archive.org/details/mathematicalpsych00edgeuoft",
    "wayback": "https://web.archive.org/web/*/https://archive.org/details/mathematicalpsych00edgeuoft"
  },
  "levinGE": {
    "url": "https://web.stanford.edu/~jdlevin/Econ%20202/General%20Equilibrium.pdf",
    "wayback": "https://web.archive.org/web/*/https://web.stanford.edu/~jdlevin/Econ%20202/General%20Equilibrium.pdf"
  },
  "acemoglu2009exchange": {
    "url": "https://economics.mit.edu/files/4153",
    "wayback": "https://web.archive.org/web/*/https://economics.mit.edu/files/4153"
  },
  "osborneRubinstein1994": {
    "url": "https://www.economics.utoronto.ca/osborne/igt/igt.pdf",
    "wayback": "https://web.archive.org/web/*/https://www.economics.utoronto.ca/osborne/igt/igt.pdf"
  }
}
```

