

# **A Unified Knowledge Base for Neoclassical and Emergence-First Economic Modeling: Theory, Computation, and Pedagogy**

## **Part I: The Neoclassical Paradigm: Equilibrium and Optimality**

The neoclassical paradigm serves as the foundation of modern microeconomic theory. It is a "top-down" framework characterized by its focus on individual optimization under constraints and the analysis of market-level equilibrium states. This paradigm provides the essential theoretical architecture against which alternative, "bottom-up" approaches can be understood and contrasted. Its rigorous mathematical structure, centered on concepts of rationality and efficiency, has shaped economic analysis for over a century.

### **Section 1: Foundations of Rational Choice**

At the heart of the neoclassical paradigm is the model of the rational agent, an abstract decision-maker who seeks to achieve the best possible outcome given their objectives and constraints. This section details the axiomatic basis of this behavior for the two principal actors in the economy: the consumer and the producer. It establishes the mathematical formalism of optimization that underpins the entire framework.

#### **1.1 Consumer Theory: Preferences, Utility, and Demand**

The theory of the consumer begins with a formal description of the individual's tastes and preferences, which are then used to model their choices in the marketplace.

**Core Concepts:** The fundamental building block of consumer theory is the concept of a preference relation, typically denoted by $\succeq$, which allows an agent to rank different consumption bundles.1 To be considered "rational" in the economic sense, these preferences must satisfy several key axioms:

* **Completeness:** For any two bundles $x$ and $y$, the consumer can rank them, such that either $x \succeq y$ or $y \succeq x$.  
* **Transitivity:** For any three bundles $x$, $y$, and $z$, if $x \succeq y$ and $y \succeq z$, then it must be that $x \succeq z$.  
* **Reflexivity:** Any bundle $x$ is at least as good as itself, $x \succeq x$.1

When these axioms, along with a continuity assumption, are met, the preference relation can be represented by a continuous utility function, $u(\cdot)$. This function assigns a numerical value to each consumption bundle such that if bundle $x$ is preferred to bundle $y$, then $u(x) > u(y)$.1 This representation transforms the problem of choice from one of abstract ranking to a mathematically tractable optimization problem.2

The Utility Maximization Problem (UMP): The central problem of the consumer is to choose the most preferred bundle of goods they can afford. Formally, given a vector of prices $p$ and income $m$, the consumer solves:

$$\max_{x} u(x) \quad \text{subject to} \quad p \cdot x \leq m$$

The solution to this problem, denoted $x(p, m)$, is the consumer's Marshallian (or uncompensated) demand function. It specifies the quantity of each good the consumer will purchase at given prices and income.3  
The Expenditure Minimization Problem (EMP): A dual perspective on the consumer's problem is to ask: what is the minimum amount of money required to achieve a specific level of utility? Given prices $p$ and a target utility level $\bar{u}$, the consumer solves:

$$\min_{x} p \cdot x \quad \text{subject to} \quad u(x) \geq \bar{u}$$

The solution to this problem, denoted $h(p, \bar{u})$, is the consumer's Hicksian (or compensated) demand function. It specifies the quantity of each good the consumer would purchase to achieve a target utility level at the lowest possible cost.3  
The relationship between these two problems is fundamental. The duality between maximization and minimization is not merely a mathematical convenience; it is the core engine for comparative statics and welfare analysis. For instance, the Slutsky equation, which decomposes the effect of a price change into substitution and income effects, is derived directly from this dual relationship. This structure is what allows for the rigorous measurement of welfare changes (e.g., compensating and equivalent variation), which depend on understanding how much income is needed to hold utility constant—a concept derived directly from the expenditure minimization problem. The canonical graduate-level treatments of these topics are found in Jehle and Reny's *Advanced Microeconomic Theory* and Mas-Colell, Whinston, and Green's (MWG) *Microeconomic Theory*.1

#### **1.2 Producer Theory: Technology, Cost, and Supply**

Parallel to the consumer, the producer (or firm) is modeled as a rational agent that makes optimal decisions, in this case concerning the transformation of inputs into outputs.

**Core Concepts:** The firm's technological capabilities are described by its **production possibility set**, $Y$. This set contains all technologically feasible production plans, where a production plan is a vector $y \in \mathbb{R}^L$ whose components represent the net output of each commodity. By convention, positive components denote outputs and negative components denote inputs.8 In the common case of a single output $q$ produced from a vector of $n$ inputs $x$, the technology can be represented by a **production function**, $q = f(x)$, which gives the maximum output obtainable from a given input vector.10

Key concepts describing the technology include:

* **Isoquants:** The set of all input combinations that yield a constant level of output, analogous to a consumer's indifference curve.10  
* **Marginal Rate of Technical Substitution (MRTS):** The rate at which one input can be substituted for another while holding output constant. It is the ratio of the marginal products of the two inputs.10  
* **Returns to Scale:** This property describes how output responds to a proportional increase in all inputs. Production can exhibit increasing, constant, or decreasing returns to scale.10

The Profit Maximization Problem (PMP): The primary objective of the firm in the neoclassical model is to maximize profit. Given a vector of input and output prices $p$, the firm chooses the production plan $y \in Y$ that solves:

$$\max_{y \in Y} p \cdot y$$

A crucial assumption here is that the firm is a price-taker, meaning it treats market prices as given and does not believe its actions can influence them.9 The solution to the PMP yields the firm's supply function (for its outputs) and unconditional factor demand functions (for its inputs).  
The Cost Minimization Problem (CMP): The dual problem for the producer is to find the least costly way to produce a given level of output $q$. Given input prices $w$, the firm solves:

$$\min_{x} w \cdot x \quad \text{subject to} \quad f(x) \geq q$$

The solution to this problem yields the firm's cost function, $c(w, q)$, and its conditional factor demand functions, $x(w, q)$.11 As with the consumer, this dual structure is essential for analyzing the firm's behavior and deriving key theoretical results. The standard treatments are found in Chapter 3 of Jehle and Reny and Chapter 5 of MWG.8

### **Section 2: General Equilibrium and Social Welfare**

After establishing the behavior of individual agents, general equilibrium theory aggregates these behaviors to analyze the economy as a whole. It addresses the question of how the independent, self-interested actions of many consumers and firms can be reconciled to achieve a coherent, market-clearing outcome. This section introduces the central concepts of market clearing, efficiency, and the conditions under which competitive markets achieve socially desirable outcomes.

#### **2.1 The Edgeworth Box and the Contract Curve**

The Edgeworth Box is the canonical graphical tool for analyzing a two-person, two-good pure exchange economy. It provides a complete microcosm of the entire general equilibrium project, containing all its core concepts: endowments, preferences, allocations, the tension between individual rationality and collective efficiency, and the price-mediated mechanism that resolves this tension.14

The box is constructed by superimposing the indifference maps of two individuals. The dimensions of the box represent the total available quantities of the two goods in the economy. Each point inside the box represents a specific allocation of the two goods between the two individuals.16 The initial distribution of resources is known as the **initial endowment**, represented by a point $\omega$ in the box.14

An allocation is **Pareto efficient** if it is impossible to reallocate the goods to make one person better off without making the other person worse off.18 In the Edgeworth Box, these efficient allocations occur at points of tangency between the two individuals' indifference curves. At such a tangency, the slopes of the indifference curves are equal, meaning the individuals' **marginal rates of substitution (MRS)** are equalized.15

The set of all Pareto efficient allocations within the Edgeworth Box is known as the **contract curve**. It typically runs from the origin of one individual to the origin of the other.14 Logically, any voluntary trade between rational individuals should result in an allocation on the contract curve, because any point not on the curve presents an opportunity for a mutually beneficial, or **Pareto-improving**, trade.18 The set of allocations on the contract curve that are also preferred by both individuals to their initial endowment is called the **core**.14

#### **2.2 The Fundamental Theorems of Welfare Economics**

The insights from the Edgeworth Box are formalized in the two Fundamental Theorems of Welfare Economics, which represent one of the greatest intellectual achievements of the economics profession.15

The **First Fundamental Theorem of Welfare Economics** states that, under certain conditions (primarily that preferences are locally non-satiated), any competitive (Walrasian) equilibrium is Pareto efficient.15 A competitive equilibrium consists of a price vector and an allocation such that each agent is maximizing their utility given the prices, and all markets clear (supply equals demand). In the context of the Edgeworth Box, this equilibrium is a point on the contract curve where a single budget line passes through the initial endowment and is tangent to both individuals' indifference curves at that point.20 The theorem provides a formal justification for Adam Smith's "invisible hand" conjecture: the pursuit of self-interest in competitive markets can lead to a socially efficient outcome.

The **Second Fundamental Theorem of Welfare Economics** provides a converse statement. It asserts that, under additional conditions (including convexity of preferences and production sets), any Pareto efficient allocation can be supported as a competitive equilibrium, provided there is an appropriate redistribution of the initial endowments.15 This theorem has profound implications for policy, as it suggests a separation between the goals of efficiency and equity. Society can, in principle, select the most equitable or "fair" allocation on the contract curve, and then use a system of lump-sum taxes and transfers to redistribute initial endowments in such a way that the market mechanism will lead to that desired outcome.16

A deep, interactive understanding of the Edgeworth Box is pedagogically equivalent to understanding the core logic of these fundamental theorems. The box visually represents the primitive setup of a general equilibrium model, the process of exchange as a movement toward the contract curve, and the equilibrium as a unique price-supported point on that curve. The First Welfare Theorem is the statement that this equilibrium point must lie on the contract curve. The Second Welfare Theorem is the statement that any point on the contract curve can be reached by finding the common tangent line at that point and adjusting the initial endowments to lie on that line.

### **Section 3: The Dynamics of Price Formation: Stability and Computation**

While general equilibrium theory proves the existence of market-clearing prices, it is often silent on the process by which those prices are reached. This section critically examines the canonical story of price adjustment, its failures, and the computational approach that arose in its wake. The failure of a simple, decentralized price adjustment process is a pivotal moment in economic theory, creating a schism that leads on one hand to computational general equilibrium (CGE) and on the other to the agent-based computational economics (ACE) paradigm.

#### **3.1 The Walrasian Tâtonnement Process**

The classical story of price adjustment is the Walrasian **tâtonnement** (French for "groping") process. It is imagined as being conducted by a fictional **Walrasian auctioneer**.14 The process works as follows:

1. The auctioneer calls out a vector of prices for all goods.  
2. Agents calculate their desired consumption and production plans at these prices and report them to the auctioneer. No trade actually occurs.  
3. The auctioneer calculates the aggregate **excess demand** for each good.  
4. If excess demand is not zero for all goods, the auctioneer adjusts prices according to a simple rule: raise the price for any good with positive excess demand and lower the price for any good with excess supply.22  
5. The process repeats until an equilibrium is found where excess demand is zero in all markets. Only then does trade take place.

Early research into the stability of this process found that it is guaranteed to converge to an equilibrium (i.e., it is globally stable) under the strong assumption that all goods are **gross substitutes**. This property means that an increase in the price of any one good will not decrease the demand for any other good.22 However, this condition is highly restrictive and unlikely to hold in general economies where goods can be complements.

#### **3.2 Scarf's Counterexamples and the Problem of Instability**

The hope that the tâtonnement process would be stable for all well-behaved economies was definitively dashed by Herbert Scarf in 1960\. Scarf constructed simple, fully specified exchange economies with rational agents and standard convex preferences that satisfied all the assumptions for the existence of an equilibrium. However, when subjected to the tâtonnement price adjustment process, these economies did not converge. Instead, the price dynamics were unstable, exhibiting persistent cycles or chaotic behavior that never reached the equilibrium.22

Scarf's counterexamples were a profound challenge to the descriptive power of general equilibrium theory. They demonstrated that the "invisible hand," if interpreted as a dynamic price-adjustment process, might not be reliable. The existence of an equilibrium did not guarantee that the market could actually find it through a plausible, decentralized process.25 This created a crisis for the theory's dynamic foundations and spurred new lines of research.

#### **3.3 Computational General Equilibrium (CGE): Scarf's Algorithm**

In response to the instability of tâtonnement, Scarf himself pioneered a new approach. Instead of modeling a dynamic adjustment process, he developed a constructive, algorithmic method for directly *computing* the equilibrium price vector.26 This work founded the field of **Computable General Equilibrium (CGE)**.

Scarf's algorithm is fundamentally different from tâtonnement. It draws on concepts from algebraic topology, such as Brouwer's Fixed-Point Theorem and Sperner's Lemma. The algorithm works by creating a simplicial subdivision of the price space and assigning a label to each vertex based on the sign of the excess demand function. It then follows a "path" of adjacent simplices until it finds one that is "completely labeled," which corresponds to an approximate fixed point of the excess demand function—and thus, an approximate equilibrium.26 Unlike tâtonnement, this path-following technique is guaranteed to converge to an equilibrium under general conditions.27

This work represented a major shift in focus, from proving the abstract *existence* of equilibrium to developing practical methods for its *computation*. It saved the equilibrium concept by making it computationally accessible, even if the dynamic process for reaching it remained elusive. This led to one of the two major intellectual responses to the crisis of tâtonnement instability. The CGE path accepts the equilibrium concept but replaces the decentralized auctioneer with a centralized computational algorithm. The other response, which forms the basis of Part III of this report, was to question the entire premise of a central price-setter and hyper-rationality, leading to the emergence-first paradigm where dynamics are the primary object of study.

## **Part II: Game Theory and Models of Strategic Interaction**

While general equilibrium theory models markets as large, anonymous arenas where individual agents are price-takers, game theory provides the tools to analyze situations of **strategic interaction**. In these settings, a small number of agents are aware of their interdependence and must account for the actions and reactions of others when making their own decisions. This part covers foundational models of bargaining, matching, and markets with imperfect information, which are essential components of modern microeconomic theory.

### **Section 4: The Bargaining Problem: Axiomatic and Strategic Foundations**

Bargaining theory addresses a fundamental economic problem: how do two or more rational agents agree to divide a surplus (a "pie") when they have conflicting interests? This section explores two distinct approaches: the axiomatic approach, which defines a "fair" or "reasonable" solution based on a set of desirable properties, and the strategic approach, which models the explicit, dynamic process of negotiation. These different philosophies provide complementary perspectives on what determines a bargaining outcome.

#### **4.1 The Nash Bargaining Solution (Axiomatic)**

John Nash's 1950 paper, "The Bargaining Problem," founded the axiomatic approach to bargaining.28 The problem is defined abstractly by a pair $(S, d)$, where $S$ is the set of feasible utility payoffs the players can achieve through agreement (assumed to be convex and closed), and $d$ is the disagreement point, representing the payoffs they receive if they fail to agree.30

Nash proposed that a reasonable solution should satisfy four axioms 30:

1. **Pareto Optimality:** The solution must be on the upper-right boundary of $S$; no other feasible agreement can make at least one player better off without making the other worse off.  
2. **Symmetry:** If the problem is symmetric (i.e., players are indistinguishable in terms of their feasible payoffs and disagreement point), the solution must give them equal utility payoffs.  
3. **Invariance to Positive Affine Transformations:** The solution should not change if one player's utility function is rescaled (e.g., from Fahrenheit to Celsius). This means utility is treated as an ordinal, von Neumann-Morgenstern measure, not a cardinal one.  
4. **Independence of Irrelevant Alternatives (IIA):** If a solution is chosen from a large set of possibilities $S$, and the set is then shrunk to a smaller set $S'$ that still contains the original solution, then the original solution must remain the solution for the smaller problem. In essence, alternatives that were not chosen should not affect the outcome.

Nash proved that there is a unique solution that satisfies these four axioms: it is the point $(u_1^*, u_2^*)$ in $S$ that maximizes the Nash product of the players' gains from agreement:

$$(u_1^* - d_1)(u_2^* - d_2)$$

The Nash solution is thus determined by a set of abstract principles of logical consistency.30

#### **4.2 The Kalai-Smorodinsky Solution (Axiomatic)**

The most controversial of Nash's axioms is the IIA. In 1975, Ehud Kalai and Meir Smorodinsky proposed an alternative solution that replaces IIA with a different axiom, **Individual Monotonicity**.32 This axiom states that if the set of feasible agreements expands in a way that is unambiguously favorable to one player (i.e., for any given payoff to the other player, the maximum payoff they can achieve is now higher), then that player's payoff in the solution should not decrease.32

This seemingly intuitive axiom of fairness leads to a different solution. The **Kalai-Smorodinsky (KS) solution** is found by identifying the **utopia point**, $u(S,d)$, which represents the maximum payoff each player could achieve individually. The solution is then the unique Pareto optimal point that lies on the straight line connecting the disagreement point $d$ to the utopia point $u(S,d)$.32 Geometrically, this means the KS solution is the point that equalizes the players' proportional gains relative to their maximum possible gains.32

#### **4.3 The Rubinstein Alternating Offers Model (Strategic)**

In contrast to the axiomatic approach, the strategic approach models the explicit procedure of bargaining. The seminal model in this tradition is Ariel Rubinstein's 1982 alternating offers game.37

The model considers two players bargaining over the division of a pie of size 1\. The process unfolds over an infinite series of discrete time periods.

* In period 1, Player 1 makes an offer.  
* Player 2 can either accept the offer (ending the game) or reject it.  
* If Player 2 rejects, the game moves to period 2, where Player 2 makes a counter-offer.  
* This process of alternating offers continues indefinitely.37

The crucial element is that delay is costly. Players have **time preferences**, captured by discount factors $\delta_1, \delta_2 \in (0,1)$. A dollar received in the next period is worth only $\delta$ of a dollar today.37 The unique **subgame perfect equilibrium (SPE)** of this game involves an immediate agreement in the first period. The equilibrium division depends critically on the players' relative patience: the player who is more patient (has a higher discount factor) is in a stronger bargaining position and receives a larger share of the pie.43 The solution also demonstrates a **first-mover advantage**; the player who makes the initial offer gets a larger share than they would if they were the responder.44

These three models are not simply alternatives; they represent an intellectual progression. The Rubinstein model can be seen as providing a non-cooperative "microfoundation" for the axiomatic Nash solution. A key result in game theory, known as the "Nash Program," shows that as the time between offers in the Rubinstein game shrinks to zero (or equivalently, as both players' discount factors approach 1), the unique SPE outcome converges to the symmetric Nash bargaining solution.31 This suggests that the abstract axioms of the cooperative Nash model can be justified as the emergent outcome of a fully specified, non-cooperative strategic game. An effective educational module should reflect this relationship, perhaps by first introducing the axiomatic solutions and then revealing the Rubinstein model as a dynamic process that can generate them.

#### **Table 1: Comparative Analysis of Bargaining Solutions**

| Feature | Nash Bargaining Solution | Kalai-Smorodinsky Solution | Rubinstein Alternating Offers |
| :---- | :---- | :---- | :---- |
| **Approach** | Axiomatic (Cooperative) | Axiomatic (Cooperative) | Strategic (Non-Cooperative) |
| **Key Axiom/Concept** | Independence of Irrelevant Alternatives (IIA) | Individual Monotonicity | Subgame Perfect Equilibrium (SPE) |
| **Core Principle** | Maximizes product of gains: $(u_1-d_1)(u_2-d_2)$ | Equalizes proportion of maximal gains | First-mover & patience advantage |
| **Information Required** | Feasible set $S$, Disagreement point $d$ | $S$, $d$, and Utopia Point $u(S,d)$ | Full game tree, Discount factors $\delta_1, \delta_2$ |
| **Key Result** | Unique point maximizing Nash product. | Unique point on line from $d$ to $u(S,d)$. | Unique SPE with immediate agreement. |
| **Primary Determinant** | Logical consistency of axioms. | Axiomatic notion of fairness/proportionality. | Strategic power from patience and procedure. |

### **Section 5: Matching Markets and Stable Allocations**

This section examines two-sided markets where price is not the sole, or even primary, mechanism for allocation. Examples include the matching of students to colleges, medical residents to hospitals, or individuals in a marriage market. In these settings, the central concept is not price-mediated market clearing, but **stability**—an allocation where there are no pairs of agents who would mutually prefer to be matched with each other over their current assignments.

#### **5.1 The Stable Marriage Problem**

The canonical model for two-sided matching is the Stable Marriage Problem, first formalized by David Gale and Lloyd Shapley in 1962\.46 The setup involves two disjoint and equal-sized sets of agents, conventionally called "men" and "women." Each agent has a strict preference ranking over all members of the opposite set.50

A matching is a set of pairs, one from each set, such that every agent is in exactly one pair. A matching is defined as **unstable** if there exists a "blocking pair": a man and a woman who are not matched to each other but who both prefer each other to their partners in the current matching. A matching is **stable** if no such blocking pair exists.50 An unstable matching is inherently fragile, as the blocking pair has an incentive to defect from their assigned partners and form a new match, potentially unraveling the entire allocation.

#### **5.2 The Gale-Shapley Deferred Acceptance Algorithm**

The key contribution of Gale and Shapley was to provide a constructive algorithm that is guaranteed to find a stable matching for any set of preferences. This is the **Deferred Acceptance (DA) algorithm**.50 One version of the algorithm proceeds as follows:

1. **Round 1:** Each man proposes to his most-preferred woman. Each woman reviews the proposals she has received, "holds on" to her most-preferred suitor, and rejects all others. She is now provisionally matched.  
2. **Round k:** Any man who was rejected in the previous round proposes to his next-most-preferred woman. Each woman again reviews all proposals she has (her current provisional match and any new ones), holds on to her most-preferred suitor among this new set, and rejects the rest.  
3. **Termination:** The algorithm continues until no man is rejected. At this point, all provisional matches become final.50

This algorithm has several remarkable properties. First, it is guaranteed to terminate and produce a stable matching.50 Second, the resulting matching is **proposer-optimal**. This means that every agent on the proposing side (in this case, the men) achieves the best possible partner they could have in *any* stable matching. Conversely, the matching is **receiver-pessimal**; every agent on the receiving side (the women) gets the worst possible partner they could have in any stable matching.50

#### **5.3 External Stability and Dynamics**

The Gale-Shapley algorithm provides a powerful and elegant solution to a complex allocation problem within a closed system. However, the stability it guarantees is static and conditional on a fixed population of agents. Research has shown that this stability can be remarkably fragile. The introduction of new agents into the market can completely disrupt the existing stable matching, potentially triggering a "cascade of divorces" where the original matches are entirely undone.51

This concept of "external stability" reveals a crucial tension. The DA algorithm produces an optimal equilibrium for a closed system, but this equilibrium is highly sensitive to the system's boundaries. This fragility provides an important link between the world of static mechanism design and the study of open, evolving systems that is central to the emergence-first paradigm. It suggests that a truly robust understanding of matching systems must account for dynamics like entry and exit, a core feature of many agent-based models.

### **Section 6: Markets with Frictions: Search and Price Dispersion**

The standard competitive model predicts that a single price—the "law of one price"—should prevail for any homogeneous good. Yet, casual observation reveals that this is often not the case; different sellers frequently charge different prices for the exact same item.52 This section analyzes how informational frictions, specifically the cost for consumers to discover prices, can fundamentally alter market outcomes and generate persistent price dispersion as a rational equilibrium phenomenon.

#### **6.1 The Law of One Price and the Challenge of Dispersion**

The puzzle of price dispersion presents a direct challenge to the frictionless neoclassical model. Explaining this phenomenon requires moving beyond the assumption of perfect information. The key insight, originating with Stigler, is that information is a resource, and acquiring it is costly. When consumers must expend time or money to learn about prices, they will not become perfectly informed. This imperfect information on the consumer side creates an opportunity for firms to exercise market power.52

#### **6.2 The Burdett-Judd Model of "Noisy" Search**

The model of Kenneth Burdett and Kenneth Judd (1983) provides a canonical explanation for equilibrium price dispersion in an environment with identical, rational agents on both sides of the market.52

The model's environment consists of a large number of identical firms (sellers) and identical consumers (buyers) for a homogeneous good. The crucial innovation lies in the information structure, or what is termed **"noisy" search**. It is assumed that when consumers decide to search, some will receive only one price quotation, while others will receive two (or more).52 This simple assumption endogenously creates two types of consumers in the market from an *ex post* perspective:

* **Captive consumers:** Those who observe only one price and must either buy at that price or not at all.  
* **Shoppers:** Those who observe two or more prices and can buy from the cheapest firm.

This structure makes a single-price equilibrium impossible. If all firms were to charge the same price, any individual firm would have an incentive to deviate by raising its price slightly. It would lose all the "shoppers," but it could extract a higher profit from its captive consumers, making the deviation profitable.53

The only stable outcome is a non-degenerate **distribution of prices**. In this equilibrium, firms are indifferent over a range of prices. The equilibrium price distribution, $F(p)$, is constructed such that the expected profit is the same for any price charged within its support. Firms that charge a high price have a high profit margin but a low probability of making a sale (they sell only to their captive customers). Firms that charge a low price have a low profit margin but a high probability of making a sale (they sell to their captive customers *and* to any shoppers who also sample a higher-priced firm).57 The equilibrium is thus characterized by a trade-off between price and quantity that equalizes profits across all active pricing strategies.

The Burdett-Judd model is a masterful example of how heterogeneity in outcomes (price dispersion) can emerge endogenously from the strategic interactions of perfectly identical and rational agents. The dispersion is not caused by *ex ante* differences in firms or consumers but is an emergent property of the market's informational structure. This represents a significant step away from simple representative agent models and toward the agent-based perspective, where the structure of interaction is a key determinant of aggregate outcomes.

## **Part III: The Emergence-First Paradigm: Agent-Based Computational Economics (ACE)**

This part of the report introduces the "bottom-up" paradigm of Agent-Based Computational Economics (ACE). This approach fundamentally challenges the core assumptions of the neoclassical model—namely, hyper-rationality, the focus on equilibrium, and the abstraction of the price formation process. ACE focuses on how complex, aggregate economic phenomena can emerge from the local interactions of heterogeneous, boundedly rational agents operating in computationally specified environments.

### **Section 7: The Bounds of Reason: A Critique of the Neoclassical Consensus**

The intellectual motivation for the shift to agent-based modeling stems from deep-seated critiques of the foundational assumptions of the neoclassical paradigm. These critiques question both the behavioral realism of the rational actor model and the institutional realism of the market-clearing process.

#### **7.1 Gintis and the Unification of the Behavioral Sciences**

In his work *The Bounds of Reason: Game Theory and the Unification of the Behavioral Sciences*, Herbert Gintis argues that the behavioral sciences are in disarray because they lack a unified model of human behavior.61 He presents a powerful critique of the **Bayesian rational actor model** (also known as the beliefs, preferences, and constraints model), arguing that it is an incomplete and often empirically falsified depiction of human decision-making.61

Gintis advocates for a new synthesis that integrates insights from across the behavioral sciences, including psychology (bounded rationality), sociology (the internalization of social norms), and biology (gene-culture coevolution).61 While he sees game theory as the essential "universal lexicon" for analyzing strategic interaction, he argues that it is insufficient on its own. Game theory without a broader social theory to explain how agents form beliefs, acquire preferences, and coordinate on norms is merely an exercise in abstract mathematics.61 This call for a more empirically grounded and interdisciplinary model of the human agent provides a strong philosophical underpinning for the ACE approach, which explicitly models agents with learning capabilities and social context.

#### **7.2 The Fable of the Auctioneer: Alternatives to Walrasian Price Formation**

As discussed in Section 3, the Walrasian auctioneer is a theoretical fiction designed to solve the problem of price determination in general equilibrium models. A growing body of research, heavily influenced by the results of laboratory experiments, critiques this centralized metaphor and proposes that price formation is a decentralized, emergent process.21

This alternative view, rooted in the classical tradition of Adam Smith and the experimental work of Vernon Smith, argues that orderly markets and stable prices emerge from the "higgling and bargaining" of privately informed, interacting agents.21 Laboratory experiments consistently show that even small numbers of unsophisticated subjects can converge to the competitive equilibrium price and quantity in double auction markets, achieving high levels of efficiency without any central coordinator.21 This suggests that the market institution itself performs the computational work that the Walrasian auctioneer was hypothesized to do. This provides a direct motivation for building agent-based models that simulate this decentralized process, shifting the focus from the properties of a pre-supposed equilibrium to the dynamics of price discovery.

The move to Agent-Based Computational Economics, therefore, is not merely a preference for a different set of tools; it represents a fundamental philosophical shift in the object of study. It is a constructive response to the core conceptual problems of the neoclassical paradigm, shifting the focus from "what is the equilibrium?" to "what macro-regularities emerge from these micro-level interactions?"

#### **Table 2: A Taxonomy of Economic Modeling Paradigms**

| Dimension | Neoclassical / Game Theory Paradigm | Agent-Based / Emergence-First Paradigm |
| :---- | :---- | :---- |
| **Core Unit** | The rational agent (homo economicus). | The autonomous, heterogeneous agent. |
| **Rationality** | Maximizing, optimizing, unbounded cognitive capacity. | Boundedly rational, adaptive, learning via heuristics. |
| **Equilibrium** | Central organizing concept; focus on existence, uniqueness, and stability of equilibrium states. | An emergent outcome, if it exists at all; focus is on the dynamic process, not the end state. |
| **Dynamics** | Often abstracted away (tâtonnement) or modeled as convergence to a known equilibrium. | The primary object of study; history-dependent, path-dependent evolution from initial conditions. |
| **Heterogeneity** | Often suppressed (representative agent) or limited to a few "types." | Embraced as a key driver of system dynamics. |
| **Methodology** | Deductive, analytical, theorem-proof. | Computational, inductive, simulation-based ("culture dish"). |
| **Key Question** | What are the properties of the equilibrium state? | What aggregate patterns emerge from local interactions? |

### **Section 8: Foundational Models of Economic Emergence**

This section presents two seminal models that exemplify the power of the emergence-first paradigm. Each model demonstrates how a fundamental economic institution—market efficiency and money, respectively—can arise from the bottom-up interactions of simple, non-optimizing agents, without the need for the strong assumptions of the neoclassical framework. These models show that complex, functional, and seemingly "intelligent" macro-level phenomena can be generated from micro-level agents who possess neither the global information nor the intention to create them.

#### **8.1 Gode & Sunder: The Emergence of Market Efficiency**

In a landmark 1993 paper in the *Journal of Political Economy*, Dhananjay Gode and Shyam Sunder investigated the source of the high allocative efficiency observed in experimental double auction markets.69 They conducted a computational experiment where they replaced profit-maximizing human traders with "Zero-Intelligence" (ZI) traders. These ZI traders were simple computer programs that generated random bids and offers, without any learning, memory, or profit-seeking motive.69

The key experiment compared two types of ZI traders: unconstrained traders who could make any random offer, and budget-constrained traders who were forbidden from making a loss-making trade (i.e., they could not bid more than their private valuation or offer to sell for less than their private cost).69 The results were striking:

* Markets with **unconstrained** ZI traders showed no tendency toward equilibrium and had low efficiency.  
* Markets with **budget-constrained** ZI traders, despite the agents' complete lack of intelligence, consistently achieved near-100% allocative efficiency, a level comparable to that achieved by rational human subjects.69

The powerful conclusion, encapsulated in the paper's subtitle, is that the **market institution acts as a partial substitute for individual rationality**.70 The high efficiency of the double auction market derives primarily from its structure—specifically, the discipline imposed by the budget constraint and the market rules—rather than from the cognitive sophistication or profit-maximizing behavior of the individual traders.69 This result challenges the neoclassical emphasis on individual rationality as the source of market order and highlights the causal power of the institutional environment itself.

#### **8.2 Kiyotaki & Wright: The Emergence of Money**

The existence and use of money is a fundamental economic phenomenon. While neoclassical models often incorporate money by placing it directly into an agent's utility function or by imposing a cash-in-advance constraint, these are top-down explanations that do not explain how money arises in the first place.76 The search-theoretic model of Nobuhiro Kiyotaki and Randall Wright (1989) provides a foundational bottom-up explanation for the emergence of a medium of exchange.77

The model considers an economy of specialized agents who are randomly matched in pairs over time. Trade can only occur if there is a "double coincidence of wants," meaning each trader has the good the other desires. The model is specifically constructed so that this double coincidence never occurs in direct barter.77 This friction creates a potential role for an intermediary good.

The model demonstrates how a **commodity money** can emerge endogenously. An agent might choose to accept a good that they do not intend to consume (e.g., a good with low storage costs) in the "speculative" belief that this good will be more easily traded for their desired consumption good in a future encounter. If enough agents adopt this belief, it becomes self-fulfilling, and the good acquires a function as a medium of exchange purely because it is believed to be acceptable by others.77 The "moneyness" of a good is shown to depend on a combination of its intrinsic physical properties (like storability) and these extrinsic, self-reinforcing beliefs about its general acceptability.77 This model provides a powerful micro-foundation for the transactions role of money, showing how it can emerge from the decentralized interactions of agents trying to overcome the frictions of barter.

### **Section 9: The ACE Methodology: A Constructive Approach to Economic Theory**

This section formalizes the principles of the Agent-Based Computational Economics paradigm, drawing heavily on the methodological contributions of Leigh Tesfatsion. It provides the conceptual framework for building, analyzing, and understanding the "emergence-first" models that form a core part of the user's project plan.

#### **9.1 Defining Agent-Based Computational Economics**

Agent-Based Computational Economics (ACE) is the computational study of economic processes modeled as dynamic systems of autonomous, interacting agents.84 It is a **"bottom-up culture-dish" approach** where, starting from initial conditions specified by the modeler, the computational economy evolves over time as its constituent agents repeatedly interact with each other and their environment.86 The goal is to "grow" macroscopic regularities and phenomena from the specified micro-level interactions, rather than assuming them *a priori*.

Tesfatsion defines ACE as a specialization of a broader class of **completely Agent-Based Modeling (c-ABM)**, which is characterized by seven specific modeling principles that emphasize the constructive and historical nature of the modeled system 86:

1. **Agent Definition:** An agent is a software entity capable of affecting outcomes through its actions.  
2. **Agent Scope:** Agents can represent a wide range of entities, from individuals to institutions or even physical phenomena.  
3. **Agent Local Constructivity:** An agent's actions at any time can only be based on its local state (its own data, attributes, and methods).  
4. **Agent Autonomy:** There is no centralized, top-down controller dictating agent behavior.  
5. **System Constructivity:** The system state is determined solely by the aggregation of its constituent agent states.  
6. **System Historicity:** The system evolves from an initial state solely through the interactions of its agents over time; path-dependency is a key feature.  
7. **Modeler as Culture-Dish Experimenter:** The modeler's role is to set up the initial conditions and interaction protocols and then observe the emergent outcomes, much like a biologist observing a petri dish.

#### **9.2 Key Components of ACE Models**

ACE models are distinguished by several key architectural features that depart from the neoclassical standard:

* **Heterogeneous Agents:** A foundational principle of ACE is the explicit modeling of agent heterogeneity. Agents can differ in their preferences, information, endowments, and behavioral rules. This heterogeneity is often a primary driver of complex system dynamics.89  
* **Learning and Adaptation:** Instead of being endowed with perfect rationality and complete information, ACE agents are typically **boundedly rational**. They learn and adapt their strategies and beliefs over time based on experience, using methods that can range from simple heuristics and reinforcement learning to more sophisticated techniques drawn from machine learning and artificial intelligence.89  
* **Interaction Topologies:** The structure of agent interactions is a critical and explicit component of the model. Agents may interact through various topologies, such as random pairwise matching (as in Kiyotaki-Wright), on fixed social or economic networks, or through endogenously formed networks that co-evolve with agent behavior.89

#### **9.3 Research Objectives in ACE**

The ACE methodology is employed to pursue several distinct research objectives:

* **Explanatory Understanding (Theory Generation):** This involves using ACE models as computational laboratories to explore the potential micro-level foundations of persistently observed macro-level phenomena. The goal is to identify plausible mechanisms that could generate regularities like trade networks, social norms, or market structures.87  
* **Normative Design (Policy Analysis):** ACE models can be used to test the potential consequences of alternative institutional designs or policies in a controlled environment. For example, researchers can simulate different auction rules, market regulations, or policy interventions to assess their likely impact on efficiency, equity, and stability before real-world implementation.87

Recent surveys, such as Tesfatsion (2021), provide a comprehensive overview of the field's history, methods, and current research frontiers, serving as an essential guide for new and established researchers.90

## **Part IV: Synthesis for Evaluation and Execution**

This final part of the report serves as a bridge between the theoretical and methodological discussions of the preceding sections and the practical requirements of evaluating and executing the proposed LLM modules and vision documentation. It focuses on the specific computational tools needed for implementation and introduces a novel framework for the pedagogical design of interactive learning modules, synthesizing principles from user experience (UX) design with the challenges of teaching complex economic concepts.

### **Section 10: A Unified Computational Toolkit for Economic Modeling**

This section provides a practical guide to the numerical methods and software libraries required to implement models from both the neoclassical/game-theoretic and the emergence-first paradigms. A strong grasp of these tools is essential for translating theoretical models into executable code.

#### **10.1 Numerical Methods in Economics**

The implementation of modern economic models, particularly those involving dynamic optimization and equilibrium analysis, relies heavily on a standard set of numerical methods. Foundational texts such as Kenneth Judd's *Numerical Methods in Economics* and Miranda and Fackler's *Applied Computational Economics and Finance* provide a comprehensive overview of this toolkit.9192

Key techniques covered in these texts include:

* **Root-Finding and Solving Systems of Equations:** Methods like Newton's method and quasi-Newton methods are essential for finding equilibrium prices by solving systems of excess demand equations or for finding optimal strategies in game theory.94  
* **Optimization:** Algorithms for both unconstrained and constrained optimization are fundamental to solving the utility maximization, cost minimization, and profit maximization problems that form the bedrock of neoclassical theory.94  
* **Function Approximation:** Techniques such as polynomial interpolation, splines, and least-squares regression are used to approximate unknown value functions or policy functions in dynamic models where analytical solutions are not available.94  
* **Numerical Integration:** Methods like Gaussian quadrature and Monte Carlo integration are necessary for calculating expected values in models with uncertainty.94  
* **Dynamic Programming:** A core set of methods, including value function iteration, policy function iteration, and projection methods, are used to solve the recursive Bellman equations that characterize dynamic stochastic optimization problems, which are central to modern macroeconomics and finance.91

#### **10.2 Open-Source Libraries for Implementation (Python)**

The Python ecosystem offers a rich set of open-source libraries that facilitate the implementation of these numerical methods and economic models.

* **Game Theory with Nashpy:** The Nashpy library is a dedicated tool for the analysis of two-player strategic form games. It allows for the straightforward creation of game objects from payoff matrices and includes algorithms for computing Nash equilibria, such as support enumeration and the Lemke-Howson algorithm.107 The library is built on the standard scientific Python stack (NumPy, SciPy) and is released under a permissive CC BY 4.0 license, making it suitable for both research and educational applications.108  
* **Bargaining and Matching:** While there is no single, dominant library for all bargaining and matching problems, implementations of specific models are available in open-source repositories. For instance, repositories on platforms like GitHub contain implementations of Rubinstein's alternating offers bargaining model, often using deep reinforcement learning or other computational approaches.110 The Gale-Shapley algorithm is also frequently implemented in educational and research codebases. These resources often require adaptation but provide a strong starting point for custom implementations.  
* **Agent-Based Modeling:** For building ACE models, several established frameworks exist. In the Python ecosystem, libraries like **Mesa** and **AgentPy** provide a structured environment for creating agent-based simulations, managing agent scheduling, and collecting data. For more complex or high-performance models, it is common to build custom simulations using core libraries like NumPy and Pandas. Outside of Python, **NetLogo** remains a widely used platform, particularly for education and exploratory modeling, due to its simple programming language and integrated visualization tools.86

### **Section 11: Pedagogical Design for Interactive Economic Modules**

This section proposes a novel synthesis for the project: applying principles from modern user experience (UX) design to create more effective, interactive, and intuitive educational modules for the complex economic concepts covered in this knowledge base. The goal is to transform static, often intimidating, theoretical diagrams into dynamic learning environments.

#### **11.1 The Principle of Progressive Disclosure**

A core principle in UX design is **progressive disclosure**. This technique involves managing information complexity by presenting only the essential information or features initially, and revealing more advanced or detailed options as the user interacts with the system.112 The primary goal is to reduce cognitive load, prevent users from feeling overwhelmed, and guide them through a task or concept in a structured, step-by-step manner.112 By layering information, an interface can cater to both novice and expert users, allowing each to engage at their desired level of complexity.112 This design philosophy is not merely about hiding content; it is a pedagogical strategy that mirrors the natural process of learning, moving from simple foundations to more complex structures.

#### **11.2 Applying Progressive Disclosure to the Edgeworth Box: A Case Study**

The Edgeworth Box is a prime candidate for a pedagogical approach based on progressive disclosure. It is an information-dense visualization that layers multiple distinct economic concepts: allocation, preferences, Pareto improvement, efficiency, and competitive equilibrium. Presenting all these elements at once can be overwhelming for a learner. An interactive simulation designed with progressive disclosure can deconstruct this complexity into a manageable learning sequence.

* **Stage 1: The Basics of Allocation.** The initial interface would present only the box itself, representing the total endowments of two goods, and a single point representing the initial allocation. The user can drag this point and observe in real-time how the quantities of goods held by Agent A and Agent B change. This first layer teaches the fundamental concept of a feasible allocation in an exchange economy.17  
* **Stage 2: Introducing Preferences and Gains from Trade.** Upon user request (e.g., clicking a "Show Preferences" button), the next layer is revealed: a single indifference curve for each agent passing through the current allocation point. This immediately creates the "lens" of mutually beneficial trades, visually demonstrating the concepts of individual rationality and the potential for a Pareto improvement.16 The user can be prompted to move the allocation point into this lens to see both agents reach a higher indifference curve.  
* **Stage 3: Revealing the Locus of Efficiency.** A subsequent interaction (e.g., "Show All Efficient Points") would render the full **contract curve**. The accompanying text would explain that this curve represents the set of all tangency points where gains from trade are exhausted and the agents' marginal rates of substitution are equal.19 This clarifies the abstract concept of Pareto efficiency as a concrete geometric locus.  
* **Stage 4: Discovering the Competitive Equilibrium.** The final layer introduces a budget line that pivots around the initial endowment point. The user's task is to adjust the slope of this line (representing the relative price ratio) until it is simultaneously tangent to both agents' indifference curves at a single point on the contract curve. This interactive task allows the user to *discover* the competitive equilibrium price, providing a powerful, hands-on demonstration of how prices coordinate individual choices to achieve an efficient outcome.20

This pedagogical strategy transforms the user from a passive observer of a complex diagram into an active participant who constructs the full concept piece by piece. This active learning approach, facilitated by a well-designed interface, is more effective for building deep, intuitive understanding than traditional static methods.117 This design philosophy—of deconstructing complex models into interactive, progressively disclosed layers—can be generalized to many other economic models, providing a core design principle for the user's entire project.

## **Appendix: Foundational Bibliography and Citation Index**

This appendix provides a centralized, citation-rich index of the foundational texts and seminal papers referenced throughout this knowledge base. Each entry includes a full BibTeX citation for easy integration into reference management software, ensuring accuracy and consistency for the project team.

#### **Table 3: Foundational Bibliography and Citation Index**

| Reference | BibTeX Entry | Cited In |
| :---- | :---- | :---- |
| Burdett & Judd (1983) | @article{BurdettJudd1983, author = {Burdett, Kenneth and Judd, Kenneth L}, title = {{Equilibrium Price Dispersion}}, journal = {Econometrica}, publisher = {Econometric Society}, volume = {51}, number = {4}, pages = {955--969}, year = {1983}, month = {July}} | Section 6 |
| Gale & Shapley (1962) | @article{GaleShapley1962, author = {Gale, D. and Shapley, L. S.}, title = {College Admissions and the Stability of Marriage}, journal = {The American Mathematical Monthly}, volume = {69}, number = {1}, pages = {9--15}, year = {1962}, publisher = {Mathematical Association of America}} | Section 5 |
| Gintis (2014) | @book{Gintis2014, author = {Gintis, Herbert}, title = {{The Bounds of Reason: Game Theory and the Unification of the Behavioral Sciences}}, edition = {Revised}, publisher = {Princeton University Press}, year = {2014}, isbn = {9781400851348}} | Section 7 |
| Gode & Sunder (1993) | @article{GodeSunder1993, author = {Gode, Dhananjay K and Sunder, Shyam}, title = {{Allocative Efficiency of Markets with Zero-Intelligence Traders: Market as a Partial Substitute for Individual Rationality}}, journal = {Journal of Political Economy}, publisher = {University of Chicago Press}, volume = {101}, number = {1}, pages = {119--137}, year = {1993}, month = {February}, doi = {10.1086/261868}} | Section 8 |
| Jehle & Reny (2011) | @book{JehleReny2011, author = {Jehle, Geoffrey A. and Reny, Philip J.}, title = {{Advanced Microeconomic Theory}}, edition = {3rd}, publisher = {Pearson}, year = {2011}, isbn = {9780273731917}} | Section 1 |
| Judd (1998) | @book{Judd1998, author = {Judd, Kenneth L.}, title = {{Numerical Methods in Economics}}, publisher = {The MIT Press}, year = {1998}, isbn = {0262100711}} | Section 10 |
| Kalai & Smorodinsky (1975) | @article{KalaiSmorodinsky1975, author = {Kalai, Ehud and Smorodinsky, Meir}, title = {{Other Solutions to Nash's Bargaining Problems}}, journal = {Econometrica}, volume = {43}, number = {3}, pages = {513--518}, year = {1975}, publisher = {Wiley-Blackwell Publishing Ltd}} | Section 4 |
| Kiyotaki & Wright (1989) | @article{KiyotakiWright1989, author = {Kiyotaki, Nobuhiro and Wright, Randall}, title = {{On Money as a Medium of Exchange}}, journal = {Journal of Political Economy}, volume = {97}, number = {4}, pages = {927--954}, year = {1989}, publisher = {University of Chicago Press}, doi = {10.1086/261634}} | Section 8 |
| Mas-Colell, Whinston, & Green (1995) | @book{MWG1995, author = {Mas-Colell, Andreu and Whinston, Michael D. and Green, Jerry R.}, title = {{Microeconomic Theory}}, publisher = {Oxford University Press}, year = {1995}, isbn = {9780195102680}} | Section 1 |
| Miranda & Fackler (2002) | @book{MirandaFackler2002, author = {Miranda, Mario J. and Fackler, Paul L.}, title = {{Applied Computational Economics and Finance}}, publisher = {MIT Press}, year = {2002}, isbn = {9780262633093}} | Section 10 |
| Nash (1950) | @article{Nash1950, author = {Nash, John}, title = {{The Bargaining Problem}}, journal = {Econometrica}, volume = {18}, number = {2}, pages = {155--162}, year = {1950}, publisher = {Econometric Society}, month = {April}} | Section 4 |
| Rubinstein (1982) | @article{Rubinstein1982, author = {Rubinstein, Ariel}, title = {{Perfect Equilibrium in a Bargaining Model}}, journal = {Econometrica}, year = {1982}, volume = {50}, number = {1}, pages = {97--110}} | Section 4 |
| Scarf (1973) | @book{Scarf1973, author = {Scarf, Herbert E. and Hansen, Terje}, title = {{The Computation of Economic Equilibria}}, publisher = {Yale University Press}, year = {1973}, series = {Cowles Foundation Monograph No. 24}} | Section 3 |
| Tesfatsion & Judd (2006) | @incollection{TesfatsionJudd2006, editor = {Tesfatsion, Leigh and Judd, Kenneth L.}, title = {{Agent-Based Computational Economics: A Constructive Approach to Economic Theory}}, booktitle = {{Handbook of Computational Economics}}, series = {Handbook of Computational Economics}, volume = {2}, chapter = {16}, pages = {831--880}, year = {2006}, publisher = {Elsevier}} | Section 9 |

#### **Works cited**

1. Solutions Manual for, accessed November 1, 2025, [https://news.fbc.keio.ac.jp/\~hhayami/texts/MasColellWhinstonGreen_1995_solution.pdf](https://news.fbc.keio.ac.jp/~hhayami/texts/MasColellWhinstonGreen_1995_solution.pdf)  
2. Advanced Microeconomic Theory Solutions Jehle Reny, accessed November 1, 2025, [https://www.jornadascyt2023.sanfrancisco.utn.edu.ar/gscheduleo/51KV321/pperformt/$17KV081691/advanced+microeconomic+theory+solutions+jehle+reny.pdf](https://www.jornadascyt2023.sanfrancisco.utn.edu.ar/gscheduleo/51KV321/pperformt/$17KV081691/advanced+microeconomic+theory+solutions+jehle+reny.pdf)  
3. Deriving Marshallian and Hicksian Demand Functions (Compensated and Uncompensated Demand) \- YouTube, accessed November 1, 2025, [https://www.youtube.com/watch?v=Zrs9uSMg6Sg](https://www.youtube.com/watch?v=Zrs9uSMg6Sg)  
4. ADVANCED MICROECONOMIC THEORY, accessed November 1, 2025, [http://zalamsyah.staff.unja.ac.id/wp-content/uploads/sites/286/2019/11/1-Advanced-Microeconomic-Theory-3rd-Ed.-JEHLE-RENY.pdf](http://zalamsyah.staff.unja.ac.id/wp-content/uploads/sites/286/2019/11/1-Advanced-Microeconomic-Theory-3rd-Ed.-JEHLE-RENY.pdf)  
5. Details for: Advanced microeconomic theory / › North South University Library catalog, accessed November 1, 2025, [https://opac.northsouth.edu/cgi-bin/koha/opac-detail.pl?biblionumber=10146\&shelfbrowse\_itemnumber=20187](https://opac.northsouth.edu/cgi-bin/koha/opac-detail.pl?biblionumber=10146&shelfbrowse_itemnumber=20187)  
6. Microeconomic Theory \- IDEAS/RePEc, accessed November 1, 2025, [https://ideas.repec.org/b/oxp/obooks/9780195102680.html](https://ideas.repec.org/b/oxp/obooks/9780195102680.html)  
7. Microeconomic Theory (textbook) \- Wikipedia, accessed November 1, 2025, [https://en.wikipedia.org/wiki/Microeconomic\_Theory\_(textbook)](https://en.wikipedia.org/wiki/Microeconomic_Theory_\(textbook\))  
8. Producer Theory \- Nolan H. Miller, accessed November 1, 2025, [https://nmiller.web.illinois.edu/documents/notes/notes5.pdf](https://nmiller.web.illinois.edu/documents/notes/notes5.pdf)  
9. Producer Theory, accessed November 1, 2025, [http://web.stanford.edu/\~jdlevin/Econ%20202/Producer%20Theory.pdf](http://web.stanford.edu/~jdlevin/Econ%20202/Producer%20Theory.pdf)  
10. 1 Introduction to producer theory \- UNC Charlotte Pages, accessed November 1, 2025, [https://belkcollegeofbusiness.charlotte.edu/azillant/wp-content/uploads/sites/846/2014/12/ECON6202\_msmicroI\_ch3notes.pdf](https://belkcollegeofbusiness.charlotte.edu/azillant/wp-content/uploads/sites/846/2014/12/ECON6202_msmicroI_ch3notes.pdf)  
11. Notes on Producer Theory, accessed November 1, 2025, [https://personalpages.manchester.ac.uk/staff/Alejandro.Saporiti/notes/Producer\_Theory.pdf](https://personalpages.manchester.ac.uk/staff/Alejandro.Saporiti/notes/Producer_Theory.pdf)  
12. Producer Theory \- Nolan H. Miller, accessed November 1, 2025, [https://nmiller.web.illinois.edu/documents/notes/secondhalf.pdf](https://nmiller.web.illinois.edu/documents/notes/secondhalf.pdf)  
13. 12E004 \- Advanced Microeconomics I, accessed November 1, 2025, [https://bse.eu/sites/default/files/12E004\_Advanced\_Microeconomics\_I.pdf](https://bse.eu/sites/default/files/12E004_Advanced_Microeconomics_I.pdf)  
14. 21\. The Edgeworth Conjecture, accessed November 1, 2025, [https://faculty.fiu.edu/\~boydj/microii/microg06-l.pdf](https://faculty.fiu.edu/~boydj/microii/microg06-l.pdf)  
15. 1 A General Equilibrium Supply and Demand Framework for Demonstrating the Fundamental Theorems of Welfare Economics March 2021 \- Kennesaw State University, accessed November 1, 2025, [https://www.kennesaw.edu/coles/research/docs/spring-2021/spring-21-02.pdf](https://www.kennesaw.edu/coles/research/docs/spring-2021/spring-21-02.pdf)  
16. Edgeworth box and contract curve | Intermediate Microeconomic Theory Class Notes | Fiveable, accessed November 1, 2025, [https://fiveable.me/intermediate-microeconomic-theory/unit-7/edgeworth-box-contract-curve/study-guide/r9Fd5QL8KRjtPaki](https://fiveable.me/intermediate-microeconomic-theory/unit-7/edgeworth-box-contract-curve/study-guide/r9Fd5QL8KRjtPaki)  
17. The Edgeworth Box: Understanding Resource Allocation and Efficiency in Microeconomics, accessed November 1, 2025, [https://maseconomics.com/the-edgeworth-box-understanding-resource-allocation-and-efficiency-in-microeconomics/](https://maseconomics.com/the-edgeworth-box-understanding-resource-allocation-and-efficiency-in-microeconomics/)  
18. Edgeworth Box, accessed November 1, 2025, [https://saylordotorg.github.io/text\_introduction-to-economic-analysis/s15-01-edgeworth-box.html](https://saylordotorg.github.io/text_introduction-to-economic-analysis/s15-01-edgeworth-box.html)  
19. The Edgeworth Box \- Wolfram Demonstrations Project, accessed November 1, 2025, [https://demonstrations.wolfram.com/TheEdgeworthBox/](https://demonstrations.wolfram.com/TheEdgeworthBox/)  
20. The Edgeworth Box \- YouTube, accessed November 1, 2025, [https://www.youtube.com/watch?v=osvoVuESEKY](https://www.youtube.com/watch?v=osvoVuESEKY)  
21. Economics of Markets: Neoclassical Theory, Experiments, and ..., accessed November 1, 2025, [https://digitalcommons.chapman.edu/cgi/viewcontent.cgi?article=1291\&context=esi\_pubs](https://digitalcommons.chapman.edu/cgi/viewcontent.cgi?article=1291&context=esi_pubs)  
22. The Stability of Walrasian General Equilibrium under a Replicator Dynamic, accessed November 1, 2025, [https://www.umass.edu/preferen/gintis/evstabilityofge.pdf](https://www.umass.edu/preferen/gintis/evstabilityofge.pdf)  
23. Tatonnement Beyond Gross Substitutes? Gradient ... \- Nikhil Devanur, accessed November 1, 2025, [https://www.nikhildevanur.com/pubs/tatonnement-gradient-descent.pdf](https://www.nikhildevanur.com/pubs/tatonnement-gradient-descent.pdf)  
24. ЕК ОНОМІК А PRICE ADJUSTMENT MECHANISMS ENSURING THE STABILITY OF EQUILIBRIUM IN A MULTIDIMENSIONAL VERSION OF SCARF', accessed November 1, 2025, [https://www.business-inform.net/export\_pdf/business-inform-2011-6\_0-pages-91\_92.pdf](https://www.business-inform.net/export_pdf/business-inform-2011-6_0-pages-91_92.pdf)  
25. On the Probability of the Competitive Equilibrium Being Globally ..., accessed November 1, 2025, [https://www.cirje.e.u-tokyo.ac.jp/research/workshops/micro/micropaper04/hirota.pdf](https://www.cirje.e.u-tokyo.ac.jp/research/workshops/micro/micropaper04/hirota.pdf)  
26. Lecture 12: Scarf's Algorithm 12.1 A constructive proof of ... \- Cnr, accessed November 1, 2025, [https://webhost.services.iit.cnr.it/staff/bruno.codenotti/lecture12p.pdf](https://webhost.services.iit.cnr.it/staff/bruno.codenotti/lecture12p.pdf)  
27. Distinguished Fellow: Herbert Scarf's Contributions to Economics \- Department of Economics \- University of Minnesota, accessed November 1, 2025, [http://users.econ.umn.edu/\~tkehoe/papers/Scarf.pdf](http://users.econ.umn.edu/~tkehoe/papers/Scarf.pdf)  
28. The Bargaining Problem \- IDEAS/RePEc, accessed November 1, 2025, [https://ideas.repec.org/a/ecm/emetrp/v18y1950i2p155-162.html](https://ideas.repec.org/a/ecm/emetrp/v18y1950i2p155-162.html)  
29. Nash bargaining theory when the number of alternatives can be finite, accessed November 1, 2025, [https://research-portal.st-andrews.ac.uk/en/publications/nash-bargaining-theory-when-the-number-of-alternatives-can-be-fin/](https://research-portal.st-andrews.ac.uk/en/publications/nash-bargaining-theory-when-the-number-of-alternatives-can-be-fin/)  
30. Individual rationality and bargaining | LSE Research Online, accessed November 1, 2025, [https://eprints.lse.ac.uk/24233/1/Individual\_rationality\_and\_bargaining\_(LSERO).pdf](https://eprints.lse.ac.uk/24233/1/Individual_rationality_and_bargaining_\(LSERO\).pdf)  
31. Nash Bargaining Theory with Non-Convexity and Unique Solution \- UCR | Department of Economics, accessed November 1, 2025, [https://economics.ucr.edu/wp-content/uploads/2019/10/Tan-paper-for-10-19-09.pdf](https://economics.ucr.edu/wp-content/uploads/2019/10/Tan-paper-for-10-19-09.pdf)  
32. Kalai–Smorodinsky bargaining solution \- Wikipedia, accessed November 1, 2025, [https://en.wikipedia.org/wiki/Kalai%E2%80%93Smorodinsky\_bargaining\_solution](https://en.wikipedia.org/wiki/Kalai%E2%80%93Smorodinsky_bargaining_solution)  
33. Other Solutions to Nash's Bargaining Problems \- Northwestern Scholars, accessed November 1, 2025, [https://www.scholars.northwestern.edu/en/publications/other-solutions-to-nashs-bargaining-problems/](https://www.scholars.northwestern.edu/en/publications/other-solutions-to-nashs-bargaining-problems/)  
34. Other Solutions to Nash's Bargaining Problems, accessed November 1, 2025, [https://www.kellogg.northwestern.edu/academics-research/research/detail/1975/other-solutions-to-nashs-bargaining-problems/?p=1](https://www.kellogg.northwestern.edu/academics-research/research/detail/1975/other-solutions-to-nashs-bargaining-problems/?p=1)  
35. Bargaining with endogenous disagreement: the extended Kalai ..., accessed November 1, 2025, [https://cris.maastrichtuniversity.nl/files/1619512/content](https://cris.maastrichtuniversity.nl/files/1619512/content)  
36. THE KALAI-SMORODINSKY SOLUTION IN LABOR- MARKET NEGOTIATIONS \- ifo Institut, accessed November 1, 2025, [https://www.ifo.de/DocDL/cesifo\_wp941.pdf](https://www.ifo.de/DocDL/cesifo_wp941.pdf)  
37. Alternating offers bargaining with loss aversion \- Maastricht University, accessed November 1, 2025, [https://cris.maastrichtuniversity.nl/files/1550510/guid-bb24a5db-4838-4583-8f60-a0750afe4fb5-ASSET1.0.pdf](https://cris.maastrichtuniversity.nl/files/1550510/guid-bb24a5db-4838-4583-8f60-a0750afe4fb5-ASSET1.0.pdf)  
38. Economics Bulletin, 2014, Vol. 34 No. 3 pp. 1611-1617 \- AccessEcon.com, accessed November 1, 2025, [http://www.accessecon.com/Pubs/EB/2014/Volume34/EB-14-V34-I3-P145.pdf](http://www.accessecon.com/Pubs/EB/2014/Volume34/EB-14-V34-I3-P145.pdf)  
39. (PDF) Perfect Equilibrium in A Bargaining Model \- ResearchGate, accessed November 1, 2025, [https://www.researchgate.net/publication/4895168\_Perfect\_Equilibrium\_in\_A\_Bargaining\_Model](https://www.researchgate.net/publication/4895168_Perfect_Equilibrium_in_A_Bargaining_Model)  
40. Perfect Equilibrium in a Bargaining Model \- Jose M. Vidal, accessed November 1, 2025, [https://jmvidal.cse.sc.edu/lib/rubinstein82a.html](https://jmvidal.cse.sc.edu/lib/rubinstein82a.html)  
41. CHAPTER 6 \- Choice of conjectures in a bargaining game with incomplete information \- Ariel Rubinstein, accessed November 1, 2025, [https://arielrubinstein.tau.ac.il/papers/17.pdf](https://arielrubinstein.tau.ac.il/papers/17.pdf)  
42. A Bargaining Model with Incomplete Information About Time Preferences \- Ariel Rubinstein, accessed November 1, 2025, [https://www1.cmc.edu/pages/faculty/MONeill/math188/papers/rubinstein5.pdf](https://www1.cmc.edu/pages/faculty/MONeill/math188/papers/rubinstein5.pdf)  
43. Rubinstein bargaining model \- Wikipedia, accessed November 1, 2025, [https://en.wikipedia.org/wiki/Rubinstein\_bargaining\_model](https://en.wikipedia.org/wiki/Rubinstein_bargaining_model)  
44. A Bargaining Game with Proposers in the Hot Seat \- MDPI, accessed November 1, 2025, [https://www.mdpi.com/2073-4336/12/4/87](https://www.mdpi.com/2073-4336/12/4/87)  
45. Kalai-Smorodinsky Bargaining Solution and Alternating Offers Game \- Scirp.org., accessed November 1, 2025, [https://www.scirp.org/journal/paperinformation?paperid=28174](https://www.scirp.org/journal/paperinformation?paperid=28174)  
46. College Admissions and the Stability of Marriage \- D. Gale; LS Shapley \- FAU Business, accessed November 1, 2025, [https://business.fau.edu/images/business/training/files/College%20admissions%20and%20stability%20of%20marriage.pdf](https://business.fau.edu/images/business/training/files/College%20admissions%20and%20stability%20of%20marriage.pdf)  
47. Gale, D. and Shapley, L. (1962) Collage Admissions and Stability of Marriage. The American Mathematical Monthly, 69, 9-15. \- References \- Scientific Research Publishing, accessed November 1, 2025, [https://www.scirp.org/reference/referencespapers?referenceid=3330434](https://www.scirp.org/reference/referencespapers?referenceid=3330434)  
48. College Admissions and Stability of Marriage \- ResearchGate, accessed November 1, 2025, [https://www.researchgate.net/publication/228108175\_College\_Admissions\_and\_Stability\_of\_Marriage](https://www.researchgate.net/publication/228108175_College_Admissions_and_Stability_of_Marriage)  
49. Gale, D. and Shapley, L. (1962) College Admission and the Stability of Marriage. American Mathematical Monthly, 69, 9-15. \- References \- Scientific Research Publishing, accessed November 1, 2025, [https://www.scirp.org/reference/referencespapers?referenceid=1258282](https://www.scirp.org/reference/referencespapers?referenceid=1258282)  
50. Stable Marriage Problem \- Digital Commons @ LIU \- Long Island ..., accessed November 1, 2025, [https://digitalcommons.liu.edu/cgi/viewcontent.cgi?article=1002\&context=post\_honors\_theses](https://digitalcommons.liu.edu/cgi/viewcontent.cgi?article=1002&context=post_honors_theses)  
51. On Gale and Shapley "college admissions and the stability of marriage" \- SciSpace, accessed November 1, 2025, [https://scispace.com/pdf/on-gale-and-shapley-college-admissions-and-the-stability-of-5fh3b9ks3f.pdf](https://scispace.com/pdf/on-gale-and-shapley-college-admissions-and-the-stability-of-5fh3b9ks3f.pdf)  
52. Equilibrium Price Dispersion \- Kenneth Burdett; Kenneth L. Judd, accessed November 1, 2025, [https://www.fc.up.pt/dmat/engmat/2011/seminario/Artigos2011/Renato\_Soeiro.pdf](https://www.fc.up.pt/dmat/engmat/2011/seminario/Artigos2011/Renato_Soeiro.pdf)  
53. Price Dispersion \- University of Edinburgh Research Explorer, accessed November 1, 2025, [https://www.research.ed.ac.uk/files/24735968/Discussion\_Paper\_1\_Price\_Dispersion.pdf](https://www.research.ed.ac.uk/files/24735968/Discussion_Paper_1_Price_Dispersion.pdf)  
54. Price Dispersion: an Evolutionary Approach \- University of Edinburgh Research Explorer, accessed November 1, 2025, [https://www.research.ed.ac.uk/en/publications/price-dispersion-an-evolutionary-approach](https://www.research.ed.ac.uk/en/publications/price-dispersion-an-evolutionary-approach)  
55. (Q,S,s) Pricing Rules Kenneth Burdett and Guido Menzio Working Paper 19094, accessed November 1, 2025, [https://www.nber.org/system/files/working\_papers/w19094/w19094.pdf](https://www.nber.org/system/files/working_papers/w19094/w19094.pdf)  
56. Burdett-Judd Redux \- IDEAS/RePEc, accessed November 1, 2025, [https://ideas.repec.org/p/red/sed015/985.html](https://ideas.repec.org/p/red/sed015/985.html)  
57. Search Theory of Imperfect Competition with Decreasing Returns to Scale\* \- Yale Department of Economics, accessed November 1, 2025, [https://economics.yale.edu/sites/default/files/2024-02/Search%20Theory%20of%20Imperfect%20Competition%20with%20Decreasing%20Returns%20to%20Scale.pdf](https://economics.yale.edu/sites/default/files/2024-02/Search%20Theory%20of%20Imperfect%20Competition%20with%20Decreasing%20Returns%20to%20Scale.pdf)  
58. Nonsequential search equilibrium with search cost heterogeneity \- VU Research Portal, accessed November 1, 2025, [https://research.vu.nl/en/publications/nonsequential-search-equilibrium-with-search-cost-heterogeneity/](https://research.vu.nl/en/publications/nonsequential-search-equilibrium-with-search-cost-heterogeneity/)  
59. Search Theory of Imperfect Competition with Decreasing Returns to Scale | NBER, accessed November 1, 2025, [https://www.nber.org/papers/w31174](https://www.nber.org/papers/w31174)  
60. Equilibrium Price Dispersion \- IDEAS/RePEc, accessed November 1, 2025, [https://ideas.repec.org/a/ecm/emetrp/v51y1983i4p955-69.html](https://ideas.repec.org/a/ecm/emetrp/v51y1983i4p955-69.html)  
61. The Bounds of Reason: Game Theory and the Unification of the ..., accessed November 1, 2025, [http://www.umass.edu/preferen/gintis/vanderschraaf.pdf](http://www.umass.edu/preferen/gintis/vanderschraaf.pdf)  
62. The Bounds of Reason: Game Theory and the Unification of the Behavioral Sciences, accessed November 1, 2025, [https://ideas.repec.org/b/pup/pbooks/10248.html](https://ideas.repec.org/b/pup/pbooks/10248.html)  
63. Herbert Gintis, The Bounds of Reason: Game Theory and the Unification of the Behavioral Sciences \- Monash University, accessed November 1, 2025, [https://research.monash.edu/en/publications/herbert-gintis-the-bounds-of-reason-game-theory-and-the-unificati](https://research.monash.edu/en/publications/herbert-gintis-the-bounds-of-reason-game-theory-and-the-unificati)  
64. The Bounds of Reason: Game Theory and the Unification of the Behavioral Sciences, accessed November 1, 2025, [https://books.google.com/books?id=fFbOAgAAQBAJ\&source=gbs\_book\_other\_versions\_r\&cad=2](https://books.google.com/books?id=fFbOAgAAQBAJ&source=gbs_book_other_versions_r&cad=2)  
65. The bounds of reason : game theory and the unification of the behavioral sciences / Herbert Gintis. \- SLV \- State Library Victoria, accessed November 1, 2025, [https://find.slv.vic.gov.au/discovery/fulldisplay?vid=61SLV\_INST%3ASLV\&docid=alma9921625343607636\&context=L](https://find.slv.vic.gov.au/discovery/fulldisplay?vid=61SLV_INST:SLV&docid=alma9921625343607636&context=L)  
66. The Bounds of Reason: Game Theory and the Unification of the Behavioral Sciences, Herbert Gintis. Princeton University Press, 2009\. xviii \+ 281 pages. | Economics & Philosophy | Cambridge Core, accessed November 1, 2025, [https://www.cambridge.org/core/journals/economics-and-philosophy/article/bounds-of-reason-game-theory-and-the-unification-of-the-behavioral-sciences-herbert-gintis-princeton-university-press-2009-xviii-281-pages/51DC74E9E306F8147656E81CE69EFCB8](https://www.cambridge.org/core/journals/economics-and-philosophy/article/bounds-of-reason-game-theory-and-the-unification-of-the-behavioral-sciences-herbert-gintis-princeton-university-press-2009-xviii-281-pages/51DC74E9E306F8147656E81CE69EFCB8)  
67. The bounds of reason: game theory and the unification of the behavioral sciences \[Revised edition\] 9780691160849, 9781400851348, 1400851343 \- DOKUMEN.PUB, accessed November 1, 2025, [https://dokumen.pub/the-bounds-of-reason-game-theory-and-the-unification-of-the-behavioral-sciences-revised-edition-9780691160849-9781400851348-1400851343.html](https://dokumen.pub/the-bounds-of-reason-game-theory-and-the-unification-of-the-behavioral-sciences-revised-edition-9780691160849-9781400851348-1400851343.html)  
68. Costs of choice: reformulating price theory without heroic assumptions \- SOAR, accessed November 1, 2025, [https://soar.wichita.edu/bitstreams/5c376e00-6ae0-4f5a-8d06-6421d047ccf4/download](https://soar.wichita.edu/bitstreams/5c376e00-6ae0-4f5a-8d06-6421d047ccf4/download)  
69. Allocative Efficiency of Markets with Zero-Intelligence Traders: Market as a Partial Substitute for Individual Rationality, accessed November 1, 2025, [https://faculty.sites.iastate.edu/tesfatsi/archive/tesfatsi/ZITraders.GodeSunder.JPE1993.pdf](https://faculty.sites.iastate.edu/tesfatsi/archive/tesfatsi/ZITraders.GodeSunder.JPE1993.pdf)  
70. Allocative Efficiency of Markets with Zero-Intelligence Traders ..., accessed November 1, 2025, [https://ideas.repec.org/a/ucp/jpolec/v101y1993i1p119-37.html](https://ideas.repec.org/a/ucp/jpolec/v101y1993i1p119-37.html)  
71. Allocative Efficiency of Markets with Zero-Intelligence Traders: Market as a Partial Substitute for Individual Rationality \- ResearchGate, accessed November 1, 2025, [https://www.researchgate.net/publication/24103759\_Allocative\_Efficiency\_of\_Markets\_with\_Zero-Intelligence\_Traders\_Market\_as\_a\_Partial\_Substitute\_for\_Individual\_Rationality](https://www.researchgate.net/publication/24103759_Allocative_Efficiency_of_Markets_with_Zero-Intelligence_Traders_Market_as_a_Partial_Substitute_for_Individual_Rationality)  
72. Zero is Not Enough: On The Lower Limit of Agent Intelligence for ..., accessed November 1, 2025, [http://www-cdr.stanford.edu/\~petrie/agents/zero\_not\_enough.pdf](http://www-cdr.stanford.edu/~petrie/agents/zero_not_enough.pdf)  
73. Zero-Intelligence Agents in Prediction Markets \- IFAAMAS, accessed November 1, 2025, [https://www.ifaamas.org/Proceedings/aamas08/proceedings/pdf/paper/AAMAS08\_0113.pdf](https://www.ifaamas.org/Proceedings/aamas08/proceedings/pdf/paper/AAMAS08_0113.pdf)  
74. Zero-Intelligence Trading in Markets \- SERC (Carleton), accessed November 1, 2025, [https://serc.carleton.edu/econ/simulations/examples/36300.html](https://serc.carleton.edu/econ/simulations/examples/36300.html)  
75. Decoupling Markets and Individuals: Rational Expectations Equilibrium Outcomes from Information Dissemination among Boundedly-Ra \- EliScholar, accessed November 1, 2025, [https://elischolar.library.yale.edu/cgi/viewcontent.cgi?article=3230\&context=cowles-discussion-paper-series](https://elischolar.library.yale.edu/cgi/viewcontent.cgi?article=3230&context=cowles-discussion-paper-series)  
76. THE TRANSACTIONS ROLE OF MONEY\* Contents ... \- ResearchGate, accessed November 1, 2025, [https://www.researchgate.net/profile/Joseph-Ostroy/publication/240203039\_Chapter\_1\_The\_transactions\_role\_of\_money/links/5cae581e299bf120975d627e/Chapter-1-The-transactions-role-of-money.pdf](https://www.researchgate.net/profile/Joseph-Ostroy/publication/240203039_Chapter_1_The_transactions_role_of_money/links/5cae581e299bf120975d627e/Chapter-1-The-transactions-role-of-money.pdf)  
77. Money Networks in Kiyotaki-Wright Model \- University of Southampton, accessed November 1, 2025, [http://www.personal.soton.ac.uk/ianni/Money\_Networks\_2013JunePDF.pdf](http://www.personal.soton.ac.uk/ianni/Money_Networks_2013JunePDF.pdf)  
78. The Origin of Money: An Agent-Based Model \- ePrints Soton \- University of Southampton, accessed November 1, 2025, [https://eprints.soton.ac.uk/355014/1/Origin\_of\_Money.pdf](https://eprints.soton.ac.uk/355014/1/Origin_of_Money.pdf)  
79. Money as a medium of exchange in an economy with artificially intelligent agents, accessed November 1, 2025, [https://experts.umn.edu/en/publications/money-as-a-medium-of-exchange-in-an-economy-with-artificially-int/](https://experts.umn.edu/en/publications/money-as-a-medium-of-exchange-in-an-economy-with-artificially-int/)  
80. On Money as a Medium of Exchange \- IDEAS/RePEc, accessed November 1, 2025, [https://ideas.repec.org/a/ucp/jpolec/v97y1989i4p927-54.html](https://ideas.repec.org/a/ucp/jpolec/v97y1989i4p927-54.html)  
81. On Money as a Medium of Exchange, accessed November 1, 2025, [http://homepage.ntu.edu.tw/\~yitingli/file/Money/KW89\_2024.pdf](http://homepage.ntu.edu.tw/~yitingli/file/Money/KW89_2024.pdf)  
82. Kiyotaki, N. and Wright, R. (1989) On Money as a Medium of Exchange. Journal of Political Economy, 97, 927-954. \- References \- Scientific Research Publishing \- Scirp.org., accessed November 1, 2025, [https://www.scirp.org/reference/referencespapers?referenceid=1194593](https://www.scirp.org/reference/referencespapers?referenceid=1194593)  
83. Money, Search and Costly Matchmaking \- Chapman University Digital Commons, accessed November 1, 2025, [https://digitalcommons.chapman.edu/cgi/viewcontent.cgi?article=1064\&context=economics\_articles](https://digitalcommons.chapman.edu/cgi/viewcontent.cgi?article=1064&context=economics_articles)  
84. Handbook of Computational Economics: Agent-Based Comput… \- Goodreads, accessed November 1, 2025, [https://www.goodreads.com/book/show/16380548-handbook-of-computational-economics](https://www.goodreads.com/book/show/16380548-handbook-of-computational-economics)  
85. (PDF) Agent-based computational economics \- ResearchGate, accessed November 1, 2025, [https://www.researchgate.net/publication/228732927\_Agent-based\_computational\_economics](https://www.researchgate.net/publication/228732927_Agent-based_computational_economics)  
86. ACE: A Completely Agent-Based Modeling Approach (Tesfatsion), accessed November 1, 2025, [https://faculty.sites.iastate.edu/tesfatsi/archive/tesfatsi/ace.htm](https://faculty.sites.iastate.edu/tesfatsi/archive/tesfatsi/ace.htm)  
87. Introductory Materials: Agent-Based Computational Economics (Tesfatsion), accessed November 1, 2025, [https://faculty.sites.iastate.edu/tesfatsi/archive/tesfatsi/aintro.htm](https://faculty.sites.iastate.edu/tesfatsi/archive/tesfatsi/aintro.htm)  
88. Agent-Based Computational Economics: Overview and Brief History1 \- Faculty Website Directory, accessed November 1, 2025, [https://faculty.sites.iastate.edu/tesfatsi/archive/tesfatsi/ACEOverviewBriefHistory.LTesfatsion.EconWP21004.LatestRevision.pdf](https://faculty.sites.iastate.edu/tesfatsi/archive/tesfatsi/ACEOverviewBriefHistory.LTesfatsion.EconWP21004.LatestRevision.pdf)  
89. faculty.sites.iastate.edu, accessed November 1, 2025, [https://faculty.sites.iastate.edu/tesfatsi/archive/tesfatsi/hbace.htm](https://faculty.sites.iastate.edu/tesfatsi/archive/tesfatsi/hbace.htm)  
90. Agent-Based Computational Economics: Overview and Brief History, accessed November 1, 2025, [https://ideas.repec.org/p/isu/genstf/202111080800001125.html](https://ideas.repec.org/p/isu/genstf/202111080800001125.html)  
91. Numerical Methods in Economics \- CUNY Graduate Center, accessed November 1, 2025, [https://www.gc.cuny.edu/sites/default/files/2021-07/Computational-Methods\_Spring\_5.pdf](https://www.gc.cuny.edu/sites/default/files/2021-07/Computational-Methods_Spring_5.pdf)  
92. Computational Economics Fall 2021, accessed November 1, 2025, [https://economics.missouri.edu/sites/default/files/grad-files/2021-09/econ-9430-hedlund-fall-2021.pdf](https://economics.missouri.edu/sites/default/files/grad-files/2021-09/econ-9430-hedlund-fall-2021.pdf)  
93. Numerical Methods in Economics by Kenneth L. Judd ... \- Booktopia, accessed November 1, 2025, [https://www.booktopia.com.au/numerical-methods-in-economics-kenneth-l-judd/book/9780262100717.html](https://www.booktopia.com.au/numerical-methods-in-economics-kenneth-l-judd/book/9780262100717.html)  
94. Numerical Methods in Economics | PDF \- Scribd, accessed November 1, 2025, [https://www.scribd.com/document/190481748/Numerical-Methods-in-Economics](https://www.scribd.com/document/190481748/Numerical-Methods-in-Economics)  
95. Numerical Methods in Economics, K.L. Judd; MIT, Press, Cambridge, MA, 1998, accessed November 1, 2025, [https://www.researchgate.net/publication/4831219\_Numerical\_Methods\_in\_Economics\_KL\_Judd\_MIT\_Press\_Cambridge\_MA\_1998](https://www.researchgate.net/publication/4831219_Numerical_Methods_in_Economics_KL_Judd_MIT_Press_Cambridge_MA_1998)  
96. Numerical Methods in Economics \- IDEAS/RePEc, accessed November 1, 2025, [https://ideas.repec.org/b/mtp/titles/0262100711.html](https://ideas.repec.org/b/mtp/titles/0262100711.html)  
97. Numerical methods in economics : Judd, Kenneth L : Free Download, Borrow, and Streaming \- Internet Archive, accessed November 1, 2025, [https://archive.org/details/numericalmethods0000judd](https://archive.org/details/numericalmethods0000judd)  
98. Judd, Kenneth L. (1998). Numerical Methods in Economics \- IDEAS/RePEc, accessed November 1, 2025, [https://ideas.repec.org/a/bla/kyklos/v52y1999i1p118-120.html](https://ideas.repec.org/a/bla/kyklos/v52y1999i1p118-120.html)  
99. accessed December 31, 1969, [https://www.google.com/search?q=Judd+Numerical+Methods+in+Economics+filetype%3Apdf](https://www.google.com/search?q=Judd+Numerical+Methods+in+Economics+filetype:pdf)  
100. Applied Computational Economics and Finance \- SciSpace, accessed November 1, 2025, [https://scispace.com/pdf/applied-computational-economics-and-finance-3srhksezt3.pdf](https://scispace.com/pdf/applied-computational-economics-and-finance-3srhksezt3.pdf)  
101. Applied Computational Economics and Finance, accessed November 1, 2025, [https://opac.feb.uinjkt.ac.id/repository/831a30a159d958fe41736d5a9dcebd03.pdf](https://opac.feb.uinjkt.ac.id/repository/831a30a159d958fe41736d5a9dcebd03.pdf)  
102. (PDF) Applied Computational Economics and Finance (2002) | Mario J. Miranda \- SciSpace, accessed November 1, 2025, [https://scispace.com/papers/applied-computational-economics-and-finance-3srhksezt3](https://scispace.com/papers/applied-computational-economics-and-finance-3srhksezt3)  
103. Applied Computational Economics and Finance \- IDEAS/RePEc, accessed November 1, 2025, [https://ideas.repec.org/b/mtp/titles/0262633094.html](https://ideas.repec.org/b/mtp/titles/0262633094.html)  
104. Applied Computational Economics and Finance, vol 1 \- EconPapers, accessed November 1, 2025, [https://econpapers.repec.org/RePEc:mtp:titles:0262633094](https://econpapers.repec.org/RePEc:mtp:titles:0262633094)  
105. Applied Computational Economics and Finance | Request PDF \- ResearchGate, accessed November 1, 2025, [https://www.researchgate.net/publication/23573634\_Applied\_Computational\_Economics\_and\_Finance](https://www.researchgate.net/publication/23573634_Applied_Computational_Economics_and_Finance)  
106. Applied Computational Economics and Finance \- Mario J. Miranda, Paul L. Fackler, accessed November 1, 2025, [https://books.google.com/books/about/Applied\_Computational\_Economics\_and\_Fina.html?id=KUYPome1SxwC](https://books.google.com/books/about/Applied_Computational_Economics_and_Fina.html?id=KUYPome1SxwC)  
107. Tutorial: building and finding the equilibrium for a game — Nashpy ..., accessed November 1, 2025, [https://nashpy.readthedocs.io/en/stable/tutorial/index.html](https://nashpy.readthedocs.io/en/stable/tutorial/index.html)  
108. (PDF) Nashpy: A Python library for the computation of Nash equilibria \- ResearchGate, accessed November 1, 2025, [https://www.researchgate.net/publication/368118641\_Nashpy\_A\_Python\_library\_for\_the\_computation\_of\_Nash\_equilibria](https://www.researchgate.net/publication/368118641_Nashpy_A_Python_library_for_the_computation_of_Nash_equilibria)  
109. Nashpy: A Python library for the computation of ... \- Open Journals, accessed November 1, 2025, [https://www.theoj.org/joss-papers/joss.00904/10.21105.joss.00904.pdf](https://www.theoj.org/joss-papers/joss.00904/10.21105.joss.00904.pdf)  
110. iwasa-kosui/predict-nash-bargaining-solution-in-negotiation-dialogue \- GitHub, accessed November 1, 2025, [https://github.com/iwasa-kosui/predict-nash-bargaining-solution-in-negotiation-dialogue](https://github.com/iwasa-kosui/predict-nash-bargaining-solution-in-negotiation-dialogue)  
111. velochy/rl-bargaining: Deep Reinforcement Learning experiments for a simple game of two-player bargaining with each player only knowing their own value \- GitHub, accessed November 1, 2025, [https://github.com/velochy/rl-bargaining](https://github.com/velochy/rl-bargaining)  
112. Progressive Disclosure UX: Making Experience Convenient | Gapsy, accessed November 1, 2025, [https://gapsystudio.com/blog/progressive-disclosure-ux/](https://gapsystudio.com/blog/progressive-disclosure-ux/)  
113. Progressive disclosure in UX design: Types and use cases \- LogRocket Blog, accessed November 1, 2025, [https://blog.logrocket.com/ux-design/progressive-disclosure-ux-types-use-cases/](https://blog.logrocket.com/ux-design/progressive-disclosure-ux-types-use-cases/)  
114. Progressive Disclosure \- The Decision Lab, accessed November 1, 2025, [https://thedecisionlab.com/reference-guide/design/progressive-disclosure](https://thedecisionlab.com/reference-guide/design/progressive-disclosure)  
115. What is Progressive Disclosure? Disclose the right information \- Octet Design Studio, accessed November 1, 2025, [https://octet.design/journal/progressive-disclosure/](https://octet.design/journal/progressive-disclosure/)  
116. Designing for Progressive Disclosure | by G. L. \- Prototypr, accessed November 1, 2025, [https://blog.prototypr.io/designing-for-progressive-disclosure-aabb5ddfbab4](https://blog.prototypr.io/designing-for-progressive-disclosure-aabb5ddfbab4)  
117. The Classroom Mini-Economy \- The University of New Mexico, accessed November 1, 2025, [https://www.unm.edu/\~jbrink/365/Documents/ClassroomEconomyBooklet.pdf](https://www.unm.edu/~jbrink/365/Documents/ClassroomEconomyBooklet.pdf)  
118. Simulations, Games and Role-play \- The Economics Network, accessed November 1, 2025, [https://www.economicsnetwork.ac.uk/handbook/printable/games\_v5.pdf](https://www.economicsnetwork.ac.uk/handbook/printable/games_v5.pdf)