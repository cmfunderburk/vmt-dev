

# **Architectural Blueprint for a Modular Protocol Engine in vmt-dev**

## **Section 1: Foundational Principles for an Extensible Simulation Engine**

This document presents a comprehensive architectural blueprint for the refactoring of the vmt-dev simulation engine. The primary objective is to evolve the current system from a rigid, monolithic structure into a flexible, extensible, and high-performance platform. This evolution is critical to achieving the project's long-term vision of supporting advanced educational and research applications by allowing for the seamless integration of novel market protocols.

### **1.1 The Case for Architectural Evolution**

The existing monolithic engine, characterized by tightly coupled components and hardcoded logic, presents significant barriers to extensibility. In a monolithic architecture, all components are combined into a single, tightly coupled piece of software.1 While this approach can be effective for initial development, it becomes a major impediment as a project's requirements evolve and scale. Any modification, such as the introduction of a new matching algorithm or search mechanism, requires direct changes to the core engine. This increases the risk of introducing bugs into stable code, complicates parallel development, and makes the system difficult for new contributors to understand and extend safely.1 This accumulated "architectural debt" directly clashes with the project's goal of becoming a versatile tool for education and research.

To overcome these limitations, a transition to a modular architecture is necessary. The foundational principles of such an architecture are Separation of Concerns, High Cohesion, and Low Coupling.2

* **Separation of Concerns:** Each module should have a single, well-defined responsibility. In the context of vmt-dev, this means the logic for how an agent *finds* a counterparty (Search) should be entirely separate from the logic that *determines the price* of a transaction (Price Formation).  
* **High Cohesion:** Functionality that is conceptually related should be grouped together within a single module. For example, all code related to a specific type of order book matching should reside in its own dedicated module.  
* **Low Coupling:** Modules should have minimal dependencies on one another. They should interact through stable, well-defined interfaces, allowing one module to be changed or replaced with minimal impact on the rest of the system.

By adhering to these principles, the refactored engine will be more maintainable, testable, and, most importantly, extensible.2

### **1.2 Selecting the Target Architecture: The Modular Monolith**

The strategic recommendation of this blueprint is the adoption of a **Modular Monolith** architecture. This modern architectural pattern strikes a pragmatic balance, combining the developmental and operational simplicity of a traditional monolith with the strong internal boundaries and extensibility of a microservices architecture.4

A Modular Monolith is a system that is structured internally as a set of loosely coupled, highly cohesive modules but is deployed as a single, unified application process.4 For vmt-dev, this approach offers several distinct advantages over both a traditional monolith and a full microservices architecture. It avoids the significant operational overhead associated with microservices—such as complex deployment pipelines, service discovery, network latency, and distributed data consistency—which would introduce unnecessary complexity for a project of this scale.4 At the same time, it enforces the strict modular boundaries that the current system lacks, allowing for independent development and testing of components.4

This architectural choice is not merely a technical preference; it is an organizational enabler. The goal of supporting educational and research contributions implies a need for a system that is easy for individuals and small teams to engage with. A full microservices architecture would present a steep learning curve and high setup costs, creating a barrier to entry for academic contributors. The Modular Monolith, by contrast, allows a researcher to focus on a single, isolated module (e.g., a new matching algorithm) with a clearly defined API, minimizing cognitive overhead and the risk of unintended side effects. This structure directly supports the project's collaborative and experimental nature by aligning the codebase's architecture with its expected contribution model.

### **1.3 Second-Order Insights & Implications**

The adoption of a Modular Monolith fosters a "composition over inheritance" philosophy at the architectural level.5 It allows different market mechanisms to be treated as components that are "plugged into" the main engine. This structure is inherently more flexible and adaptable than a rigid, inheritance-based hierarchy. It enables the creation of a platform where the core engine is stable and well-tested, while the peripheral modules—the protocols—can be experimental and rapidly iterated upon. This clear separation between a stable core and dynamic extensions is fundamental to achieving the project's long-term goals for research and education.

## **Section 2: The Core Plugin Architecture: A Scaffold for Growth**

To realize the vision of a Modular Monolith, a robust plugin architecture is required. This architecture will serve as the primary mechanism for achieving runtime extensibility, allowing new protocols to be discovered and integrated into the simulation engine dynamically. The goal is to create a system where a developer can add a new search or matching protocol simply by placing a correctly structured Python module into a designated directory, without modifying any of the engine's core code.6

### **2.1 Overview of the Plugin System**

The plugin system will be composed of three fundamental components that work in concert to provide a flexible and maintainable extension mechanism:

1. **Protocol Interface Contracts:** A set of Abstract Base Classes (ABCs) that formally define the methods and properties a class must implement to be considered a valid protocol of a certain type (e.g., SearchProtocol, MatchingProtocol). These contracts serve as the public API for all extensions.9  
2. **The Plugin Manager:** A central service responsible for the discovery, validation, and registration of plugin modules at runtime. It acts as the bridge between the core engine and the external protocol implementations.  
3. **Concrete Plugins:** The individual protocol implementations, packaged as standard Python modules. Each plugin will contain one or more classes that inherit from and implement the appropriate protocol interface contract.

### **2.2 Plugin Discovery and Registration**

The system will employ a dynamic loading mechanism to discover and register plugins at startup. This approach avoids hardcoded imports and allows the engine to remain completely decoupled from the specific plugins that are available.

The recommended implementation leverages Python's importlib library for dynamic module loading, combined with a clever registration pattern using the \_\_init\_subclass\_\_ special method.10 A base class, ProtocolBase, will be created. Any concrete protocol class that inherits from ProtocolBase will be automatically added to a central registry maintained by the base class itself. The PluginManager will then simply need to scan a designated plugins/ directory and dynamically import each Python file. The act of importing triggers the \_\_init\_subclass\_\_ hook, automatically registering the new protocol without any explicit registration code in the plugin file itself.10 This creates a simple, declarative, and elegant method for developers to create new plugins.

For more advanced use cases, particularly for third-party contributions that may be distributed as independent packages, the system can be extended to use setuptools entry points.9 This allows plugins to be installed via pip and discovered by the PluginManager through package metadata, providing a more robust and standardized distribution mechanism. The initial implementation can begin with the simpler directory-scanning approach and evolve to support entry points as needed.

### **2.3 The Plugin Manager Service**

The PluginManager is more than a simple module loader; it is the gatekeeper of the plugin ecosystem. Its core responsibilities include:

* **Discovery:** Scanning the plugins/ directory (or querying setuptools entry points) to find potential plugin modules.  
* **Validation:** After loading a module, the manager must inspect its contents to find classes that inherit from ProtocolBase. It will then validate that these classes correctly implement the full interface contract required by their specific protocol type (e.g., a SearchProtocol must have a search method). This prevents runtime errors from malformed plugins.  
* **Registration:** Maintaining a central, accessible registry of all validated and available protocols. This registry will typically be a dictionary mapping a unique protocol name (e.g., "pro\_rata\_matching") to its loaded class object.  
* **Lifecycle Management:** Handling the loading of plugins at startup. For advanced scenarios, it could also be designed to support unloading or hot-reloading of plugins, though this is not a requirement for the initial implementation.

This separation of concerns transforms the engine from a static application into a dynamic platform. The core development team can focus on the stability and performance of the main simulation loop and the PluginManager, while researchers and students can work independently on extensions, interacting with the system only through the stable, public API of the protocol interfaces. This decoupling is essential for versioning and long-term stability, as the core engine can evolve independently of the plugins, and vice-versa.9

## **Section 3: Designing the Protocol API: Search, Matching, and Beyond**

The new programming interface, or Application Programming Interface (API), is the formal contract that decouples the simulation engine from the concrete protocol implementations. A well-designed API is the cornerstone of a successful modular system. This section defines the specific interfaces for the highest-priority protocols: Search and Matching.

### **3.1 The Role of Abstract Base Classes (ABCs)**

To enforce these contracts programmatically, all protocol interfaces will be defined as Python Abstract Base Classes using the abc module. An ABC allows for the definition of methods that subclasses are required to implement.5 If a developer creates a new plugin that claims to be a SearchProtocol but fails to implement the required search method, an error will be raised when the class is defined or instantiated, rather than manifesting as a difficult-to-debug AttributeError deep within the simulation loop. This makes the system more robust, self-documenting, and easier for new developers to work with.

### **3.2 SearchProtocol Interface Definition**

The SearchProtocol interface defines the contract for any algorithm responsible for how an agent discovers potential counterparties, quotes, or orders within the market.

* **Purpose:** To encapsulate the logic of information discovery. This could range from a simple random sampling of the order book to a complex spatial search on a geographic grid or a query to a specific counterparty.  
* **Proposed Methods:**  
  * \_\_init\_\_(self, config: dict): The constructor, which receives a dictionary of protocol-specific parameters. This allows each protocol to be configured independently via the main simulation configuration file.  
  * search(self, agent: 'Agent', market: 'Market') \-\> list: The core operational method. It takes the searching agent and the current state of the market as input and must return a list of discovered objects (e.g., quotes, orders, or other agents).

### **3.3 MatchingProtocol Interface Definition**

The MatchingProtocol interface defines the contract for any algorithm that processes incoming orders and attempts to form trades. This is the heart of the market-clearing mechanism.

* **Purpose:** To encapsulate the logic of how orders are matched and trades are generated. This could implement a continuous limit order book, a frequent batch auction, a call market, or any other matching mechanism.  
* **Proposed Methods:**  
  * \_\_init\_\_(self, config: dict): The constructor for configuration, similar to the SearchProtocol.  
  * match(self, orders: list\['Order'\], order\_book: 'OrderBook') \-\> list: The core operational method. It receives a list of new orders to be processed and the current state of the order book, and it must return a list of any trades that were generated as a result of the matching logic.

### **3.4 Table: Protocol Interface Definitions**

The following table provides a formal and consolidated specification of the proposed protocol interfaces. This serves as a quick-reference guide for developers and is the canonical definition of the system's primary extension points.

| Interface | Method | Parameters | Return Type | Description |
| :---- | :---- | :---- | :---- | :---- |
| ProtocolBase | \_\_init\_\_(self, config: dict) | config: A dictionary of protocol-specific settings. | None | Initializes the protocol with parameters from the simulation config. |
| SearchProtocol | search(self, agent: 'Agent', market: 'Market') | agent: The searching agent object. market: The current market state object. | list | Executes the search algorithm and returns a list of discovered quotes/counterparties. |
| MatchingProtocol | match(self, orders: list\['Order'\], order\_book: 'OrderBook') | orders: A list of new orders to be processed. order\_book: The current state of the order book. | list | Executes the matching algorithm and returns a list of generated trades. |
| PriceFormationProtocol | form\_price(self, trade\_info: dict) | trade\_info: Data about a potential trade (e.g., matched orders). | float | Calculates and returns the final execution price for a trade. |

## **Section 4: Implementing Interchangeable Protocols via the Strategy Pattern**

With the protocol interfaces defined, the next step is to design how the core SimulationEngine will use them to achieve runtime flexibility. The **Strategy design pattern** is the ideal architectural choice for this task. It is a behavioral pattern whose intent is to define a family of algorithms, encapsulate each one, and make them interchangeable.5 This aligns perfectly with the project's need to swap out different Search, Matching, and Price Formation algorithms at runtime.

### **4.1 The Strategy Pattern Explained**

The Strategy pattern relies on three key components, which map directly to the proposed vmt-dev architecture 12:

* **Context:** This is the class that needs to perform the behavior. In this case, the SimulationEngine is the Context. It will hold a reference to a strategy object but will be completely unaware of the concrete implementation details.  
* **Strategy:** This is the common interface for all the different algorithms. The SearchProtocol and MatchingProtocol ABCs defined in the previous section serve as the Strategy interfaces.  
* **Concrete Strategy:** These are the individual classes that implement the specific algorithms. For example, GridSearchProtocol, RandomWalkSearchProtocol, ProRataMatchingProtocol, and AuctionMatchingProtocol would all be Concrete Strategies.

By using this pattern, the SimulationEngine's code can be written to depend only on the abstract SearchProtocol interface, not on any specific search algorithm. This decouples the engine's orchestration logic from the algorithmic implementation.12

### **4.2 Integrating Strategies into the SimulationEngine**

The integration is achieved through the principle of **composition over inheritance**. The SimulationEngine will not inherit the logic of any protocol. Instead, it will be *composed* of protocol objects, holding them as instance attributes (e.g., self.search\_protocol, self.matching\_protocol).

During the main simulation loop, when it is time for an agent to search the market, the engine will simply delegate the call to its configured search protocol object:  
discovered\_quotes \= self.search\_protocol.search(current\_agent, market\_state)  
This approach cleanly separates the responsibilities within the system. The SimulationEngine is responsible for the high-level orchestration of the simulation—managing time, iterating through agents, and maintaining the canonical state of the market. The protocol objects, meanwhile, are responsible for the specific, encapsulated behaviors that operate on that state. This separation prevents the engine's state management logic from becoming entangled with the algorithmic logic, a common source of bugs and complexity in monolithic systems. Furthermore, it allows the core data structures (like the market state) to be optimized independently of the algorithms that use them, which is a significant advantage for performance and scalability.

### **4.3 Code Example: The Engine as the Context**

The following Python code snippet illustrates the structure of the SimulationEngine class acting as the Context for the various protocol strategies.

Python

from typing import Type  
from protocols import SearchProtocol, MatchingProtocol \# Abstract interfaces

class SimulationEngine:  
    """  
    The Context class that uses interchangeable protocol strategies.  
    """  
    def \_\_init\_\_(self, search\_protocol: SearchProtocol, matching\_protocol: MatchingProtocol):  
        """  
        The engine is initialized with concrete strategy objects,  
        but only knows about them through their abstract interfaces.  
        """  
        self.search\_protocol \= search\_protocol  
        self.matching\_protocol \= matching\_protocol  
        self.market\_state \= self.\_initialize\_market\_state()  
        self.agents \= self.\_initialize\_agents()

    def run\_step(self):  
        """  
        Executes a single step of the simulation loop.  
        """  
        \# \--- Search Phase \---  
        for agent in self.agents:  
            \# Delegate the search behavior to the configured search protocol  
            discovered\_items \= self.search\_protocol.search(agent, self.market\_state)  
            \# Agent processes discovered items and may generate orders...  
            new\_orders \= agent.process\_search\_results(discovered\_items)

        \# \--- Matching Phase \---  
        if new\_orders:  
            \# Delegate the matching behavior to the configured matching protocol  
            generated\_trades \= self.matching\_protocol.match(new\_orders, self.market\_state.order\_book)  
            self.\_process\_trades(generated\_trades)

    def \_initialize\_market\_state(self):  
        \#... logic to set up the initial market state...  
        pass

    def \_initialize\_agents(self):  
        \#... logic to create the agent population...  
        pass

    def \_process\_trades(self, trades):  
        \#... logic to update agent portfolios and market state based on trades...  
        pass

This example demonstrates how the engine's run\_step method orchestrates the simulation by delegating to the search and match methods of the protocol objects it holds. The engine itself contains no specific logic for how searching or matching is performed.

## **Section 5: Dynamic Protocol Instantiation with the Factory Pattern**

While the Strategy pattern allows the SimulationEngine to use protocols interchangeably, a mechanism is still needed to select and create the correct protocol objects at the start of a simulation. Hardcoding this instantiation logic directly into the engine would reintroduce the tight coupling the new architecture is designed to eliminate.15 For example, code like if config\['search'\] \== 'grid': self.search\_protocol \= GridSearchProtocol() makes the engine directly aware of every possible concrete protocol, violating the Open/Closed Principle.12

The solution is to delegate the responsibility of object creation to a dedicated component. The **Factory Method design pattern** is perfectly suited for this task. It is a creational pattern that provides an interface for creating objects but lets the component that uses the objects decide which class to instantiate.15

### **5.1 The Factory Method Pattern**

In this architecture, a ProtocolFactory will be responsible for creating and configuring the set of protocol objects required for a given simulation run.17 The factory will take the simulation configuration (e.g., a dictionary loaded from a JSON or YAML file) and the PluginManager's registry of available protocols as its input. It will then parse the configuration, find the requested protocol classes in the registry, and instantiate them with their specific parameters.

This approach fully decouples the SimulationEngine from the concrete protocol classes. The engine only needs to know how to receive a set of fully configured protocol objects that adhere to the required interfaces. It has no knowledge of how they were created, where they came from, or what specific implementations they are.

It is important to adopt a Pythonic implementation of this pattern. The classic "Gang of Four" Factory Method often involves a complex hierarchy of creator classes, which is often unnecessary in a dynamic language like Python.19 For vmt-dev, the ProtocolFactory can be implemented as a single, straightforward class or even a standalone function that encapsulates the creation logic.

### **5.2 The Complete Workflow**

The combination of the Plugin Manager, Factory, and Strategy patterns creates a clean, decoupled, and fully declarative workflow for initializing and running a simulation:

1. **Startup:** The main application entry point is executed.  
2. **Plugin Discovery:** The PluginManager is initialized. It scans the plugins/ directory, dynamically loads all modules, and populates its internal registry with all available, validated protocol classes.  
3. **Configuration Loading:** The user-provided simulation configuration file (e.g., config.yaml) is loaded into a dictionary.  
4. **Factory Instantiation:** The ProtocolFactory is called, receiving the configuration dictionary and the PluginManager's protocol registry as arguments.  
5. **Protocol Creation:** The factory reads the configuration (e.g., search\_protocol: grid\_search), looks up the GridSearchProtocol class in the registry, and instantiates it with its specific parameters from the config. It repeats this for all required protocols.  
6. **Engine Initialization:** The SimulationEngine is then initialized, receiving the fully-formed and configured protocol objects from the factory.  
7. **Simulation Run:** The engine's main loop begins, delegating calls to the protocol objects as needed.

This architecture transforms vmt-dev from a system where behavior is defined by imperative code into a true simulation framework where behavior is defined by a declarative configuration file. This shift has profound implications for the project's research and educational goals. A researcher can now design and execute a completely new experiment—for example, comparing the market impact of two different matching algorithms—simply by changing a few lines in a configuration file and re-running the simulation. This dramatically accelerates the research lifecycle and makes the system a powerful instrument for scientific inquiry and a clear tool for educational demonstration.

## **Section 6: A Phased and Risk-Averse Migration Strategy**

Transitioning from a monolithic architecture to a modular one is a significant undertaking. A "big bang" rewrite, where the entire system is replaced at once, is fraught with risk and can lead to long development cycles with no deliverable value. Therefore, this blueprint advocates for a phased, incremental migration strategy that minimizes disruption to existing functionality and allows for continuous validation at each step.20

### **6.1 Guiding Principle: Incremental Refactoring**

The core principle of the migration is to refactor the system in a series of small, safe, and verifiable steps. This approach, often inspired by patterns like the Strangler Fig pattern, involves gradually replacing pieces of the old system with new services or modules while keeping the entire application functional throughout the process.20

### **6.2 Phase 1: Encapsulate and Adapt**

The objective of the first phase is to introduce the new architectural scaffolding and make the existing monolithic logic compatible with it, *without* rewriting the core algorithms immediately. This isolates the legacy code and prepares it for replacement.

* **Activities:**  
  1. **Define Interfaces:** Implement the ProtocolBase, SearchProtocol, and MatchingProtocol Abstract Base Classes as defined in Section 3\.  
  2. **Build Scaffolding:** Implement the PluginManager and ProtocolFactory components.  
  3. **Create Adapters:** For each piece of legacy logic, create an "Adapter" class. For instance, a LegacySearchAdapter will be created that implements the SearchProtocol interface. The search() method of this adapter will do nothing more than call the old, monolithic search function, translating its inputs and outputs to match the new interface definition.22 The same will be done for the matching logic with a LegacyMatchingAdapter.  
  4. **Update Engine:** Refactor the main simulation entry point to use the new initialization workflow (Plugin Manager \-\> Factory \-\> Engine). The default configuration will be set to use the newly created adapter classes.  
* **Outcome:** At the end of Phase 1, the engine will be operating via the new modular interfaces and declarative configuration system. However, since the adapters are simply calling the original code, the simulation's behavior will be identical to the old system. This provides a safe, verifiable checkpoint where the new architecture is in place but no core functionality has been altered.

### **6.3 Phase 2: Refactor and Replace**

With the legacy logic safely encapsulated behind the new interfaces, the second phase involves systematically replacing it with clean, modular, and well-tested implementations.

* **Activities:**  
  1. **Prioritize Search:** As per the project's priorities, the Search protocol will be the first to be replaced. A new, clean implementation (e.g., GridSearchProtocol) will be created as a separate plugin file.  
  2. **Isolate and Test:** This new protocol will be developed and unit-tested in complete isolation from the rest of the engine, relying only on the SearchProtocol interface contract.  
  3. **Update Configuration:** The default simulation configuration will be updated to use the new GridSearchProtocol instead of the LegacySearchAdapter.  
  4. **Regression Testing:** A suite of regression tests will be run to compare the output of simulations using the new protocol against the baseline results from Phase 1\. Any intentional behavioral changes should be documented, and any unintended discrepancies must be resolved.  
  5. **Repeat for Matching:** The same process (implement, test, switch config, validate) will be repeated for the Matching protocol, replacing the LegacyMatchingAdapter with a new, clean implementation.  
* **Outcome:** By the end of Phase 2, the core monolithic logic for search and matching will have been safely retired and replaced by new, modular, and independently tested components.

### **6.4 Phase 3: Extend and Validate**

The final phase serves as the ultimate validation of the new architecture's success by demonstrating its primary goal: extensibility.

* **Activities:**  
  1. **Implement a Novel Protocol:** A developer will implement a completely new protocol that was not part of the original system (e.g., a ReinforcementLearningSearchProtocol or a SealedBidAuctionProtocol).  
  2. **Add as a Plugin:** This new protocol will be added to the system simply by placing its Python file in the plugins/ directory. No changes will be made to the core SimulationEngine or any other part of the system.  
  3. **Run via Configuration:** A new simulation experiment will be run by creating a new configuration file that specifies the novel protocol (e.g., search\_protocol: reinforcement\_learning\_search).  
* **Outcome:** The successful execution of a simulation using a new, dynamically loaded protocol provides definitive proof that the project's goals of modularity and extensibility have been achieved.

### **6.5 Table: Phased Migration Roadmap**

The following table visualizes the migration plan, providing clear phases, deliverables, and validation criteria to guide the project management of this refactoring effort.

| Phase | Objective | Key Activities | Validation Criteria | Relevant Patterns |
| :---- | :---- | :---- | :---- | :---- |
| **1** | Isolate Legacy Code | Define protocol interfaces. Create Adapter classes for old search/match logic. Implement Plugin Manager and Factory. | Existing simulations run without modification under the new engine structure. The system is configurable. | Adapter |
| **2** | Replace Core Protocols | Implement new, clean Search & Matching protocols from scratch as plugins. Write comprehensive unit tests for each. | New protocols pass all unit tests. Regression tests show consistent or verifiably improved simulation behavior. | Strategy, Factory |
| **3** | Demonstrate Extensibility | Develop a novel third-party protocol as a plugin. Document the plugin development process. | The new protocol can be discovered and run via a simple config change, with no core code modification required. | Plugin |

## **Section 7: Analysis of Architectural Priorities and Trade-offs**

This final section evaluates the proposed Modular Monolith architecture against the project's stated priorities of Performance/Scalability, Educational Clarity, and Research Utility.

### **7.1 Primary Priority: Performance & Scalability**

A common concern with architectures that rely heavily on design patterns is the potential for performance overhead. However, in a high-level language like Python, the cost of the additional method calls involved in the Strategy pattern's delegation or the initial object creation by the Factory is negligible.12 This overhead will be orders of magnitude smaller than the computational cost of the actual simulation algorithms (e.g., complex matching or agent decision logic).

The true performance benefit of this architecture lies in its modularity. By isolating protocols into discrete, independent components, it enables targeted and high-impact performance tuning. For example, if a specific matching algorithm is identified as a computational bottleneck, it can be optimized or even rewritten in a high-performance language like Rust or C++ and wrapped as a Python extension. This high-performance module can then be plugged into the existing engine without requiring any changes to the rest of the Python-based system. This architecture, therefore, does not hinder performance; rather, it provides the ideal framework for achieving high performance and scalability in a targeted, efficient manner.

### **7.2 Secondary Priority: Educational Clarity**

For educational purposes, the proposed architecture represents a monumental improvement over a monolith. The clear separation of concerns allows an instructor or student to study a specific part of a market mechanism in isolation.2 One can understand the principles of a pro-rata matching algorithm by examining a single, self-contained ProRataMatchingProtocol module, without needing to comprehend the entire simulation engine.

Furthermore, the declarative, configuration-driven nature of the system is a powerful teaching tool. An instructor can demonstrate the profound impact of different market rules—for instance, switching from a continuous limit order book to a frequent batch auction—simply by changing a single line in a configuration file and re-running a simulation live in a classroom setting. This provides direct, interactive feedback on the consequences of different protocol designs.

### **7.3 Tertiary Priority: Research Utility**

The plugin architecture directly addresses the needs of the research community. It creates a "hot-swappable" environment for algorithms, drastically lowering the barrier to entry for testing novel hypotheses.6 A researcher can focus entirely on implementing their novel search algorithm or pricing model, confident that it will integrate seamlessly into a stable, well-defined simulation environment. This allows them to spend their time on research, not on re-engineering a complex simulation platform.

Crucially, the declarative nature of the system strongly supports scientific reproducibility. The exact conditions of a simulation experiment—including the specific versions of every protocol used and all their parameters—can be perfectly captured and shared in a single, human-readable configuration file. This makes it easy for other researchers to replicate, verify, and build upon previous work, which is a cornerstone of the scientific method.

### **7.4 Summary of Trade-offs**

The primary trade-off in adopting this architecture is an increase in structural complexity compared to a single monolithic file. Developers will need to understand the roles of and interactions between the Engine (Context), the Plugin Manager, the Factory, and the individual Protocol (Strategy) plugins. However, this is a form of "good" complexity—it is organized, principled, and designed explicitly to manage the "bad," tangled complexity of the monolithic logic it replaces.16

There is an upfront development cost associated with building this initial scaffolding. This investment, however, is essential. It will be rapidly paid back through reduced long-term maintenance costs, increased development velocity for new features, and, most importantly, the successful achievement of the project's core vision to become a flexible and powerful platform for market simulation education and research.

#### **Works cited**

1. Migrating from Monolithic to Serverless: A FinTech Case Study \- SPEC Research Group, accessed October 20, 2025, [https://research.spec.org/icpe\_proceedings/2020/companion/p20.pdf](https://research.spec.org/icpe_proceedings/2020/companion/p20.pdf)  
2. How to design modular Python projects | LabEx, accessed October 20, 2025, [https://labex.io/tutorials/python-how-to-design-modular-python-projects-420186](https://labex.io/tutorials/python-how-to-design-modular-python-projects-420186)  
3. Design Patterns in Python: A Series | 2023 \- Medium, accessed October 20, 2025, [https://medium.com/@amirm.lavasani/design-patterns-in-python-a-series-f502b7804ae5](https://medium.com/@amirm.lavasani/design-patterns-in-python-a-series-f502b7804ae5)  
4. Modular Monolith: Is This the Trend in Software Architecture? \- arXiv, accessed October 20, 2025, [https://arxiv.org/pdf/2401.11867](https://arxiv.org/pdf/2401.11867)  
5. Design Patterns in Python: Strategy | Medium, accessed October 20, 2025, [https://medium.com/@amirm.lavasani/design-patterns-in-python-strategy-7b14f1c4c162](https://medium.com/@amirm.lavasani/design-patterns-in-python-strategy-7b14f1c4c162)  
6. Implementing a Plugin Architecture in Your Python Application, accessed October 20, 2025, [https://wearecommunity.io/communities/AsdltxPyEV/articles/6735](https://wearecommunity.io/communities/AsdltxPyEV/articles/6735)  
7. Implementing a plugin architecture in Python \- Reddit, accessed October 20, 2025, [https://www.reddit.com/r/Python/comments/arv0sl/implementing\_a\_plugin\_architecture\_in\_python/](https://www.reddit.com/r/Python/comments/arv0sl/implementing_a_plugin_architecture_in_python/)  
8. Plugin Architecture for Python \- Binary Coders \- WordPress.com, accessed October 20, 2025, [https://binarycoders.wordpress.com/2023/07/22/plugin-architecture-for-python/](https://binarycoders.wordpress.com/2023/07/22/plugin-architecture-for-python/)  
9. A Python Plugin Pattern | Vinnie dot Work, accessed October 20, 2025, [https://www.vinnie.work/blog/2021-02-16-python-plugin-pattern](https://www.vinnie.work/blog/2021-02-16-python-plugin-pattern)  
10. Python: Implement basic plugin architecture with Python and ..., accessed October 20, 2025, [https://gist.github.com/dorneanu/cce1cd6711969d581873a88e0257e312](https://gist.github.com/dorneanu/cce1cd6711969d581873a88e0257e312)  
11. Become a Python Design Strategist using the Strategy Pattern \- DEV Community, accessed October 20, 2025, [https://dev.to/fayomihorace/become-a-python-design-strategist-using-the-strategy-pattern-6ad](https://dev.to/fayomihorace/become-a-python-design-strategist-using-the-strategy-pattern-6ad)  
12. Strategy Pattern: Definition, Examples, and Best Practices \- Stackify, accessed October 20, 2025, [https://stackify.com/strategy-pattern-definition-examples-and-best-practices/](https://stackify.com/strategy-pattern-definition-examples-and-best-practices/)  
13. Strategy Design Pattern in Python \- Auth0, accessed October 20, 2025, [https://auth0.com/blog/strategy-design-pattern-in-python/](https://auth0.com/blog/strategy-design-pattern-in-python/)  
14. Where is the benefit in using the Strategy Pattern? \- Stack Overflow, accessed October 20, 2025, [https://stackoverflow.com/questions/171776/where-is-the-benefit-in-using-the-strategy-pattern](https://stackoverflow.com/questions/171776/where-is-the-benefit-in-using-the-strategy-pattern)  
15. The Factory Method Pattern and Its Implementation in Python – Real ..., accessed October 20, 2025, [https://realpython.com/factory-method-python/](https://realpython.com/factory-method-python/)  
16. Factory Method Pattern in Python \- Codesarray, accessed October 20, 2025, [https://codesarray.com/view/Factory-Method-Pattern-in-Python](https://codesarray.com/view/Factory-Method-Pattern-in-Python)  
17. Python Design Patterns in Depth: The Factory Pattern \- Packt, accessed October 20, 2025, [https://www.packtpub.com/en-us/learning/how-to-tutorials/python-design-patterns-depth-factory-pattern](https://www.packtpub.com/en-us/learning/how-to-tutorials/python-design-patterns-depth-factory-pattern)  
18. Factory Design Patterns in Python \- Dagster, accessed October 20, 2025, [https://dagster.io/blog/python-factory-patterns](https://dagster.io/blog/python-factory-patterns)  
19. The Factory Method Pattern \- Python Design Patterns, accessed October 20, 2025, [https://python-patterns.guide/gang-of-four/factory-method/](https://python-patterns.guide/gang-of-four/factory-method/)  
20. Seven application modernization case studies \- vFunction, accessed October 20, 2025, [https://vfunction.com/blog/application-modernization-case-study/](https://vfunction.com/blog/application-modernization-case-study/)  
21. Safely Modernizing a Monolith with AWS Migration Hub Refactor Spaces, accessed October 20, 2025, [https://aws.amazon.com/blogs/apn/safely-modernizing-a-monolith-with-aws-migration-hub-refactor-spaces/](https://aws.amazon.com/blogs/apn/safely-modernizing-a-monolith-with-aws-migration-hub-refactor-spaces/)  
22. Design Patterns in Python \- Refactoring.Guru, accessed October 20, 2025, [https://refactoring.guru/design-patterns/python](https://refactoring.guru/design-patterns/python)  
23. Designing a plugin architecture in Python, accessed October 20, 2025, [https://python.org.il/en/presentations/designing-a-plugin-architecture-in-python](https://python.org.il/en/presentations/designing-a-plugin-architecture-in-python)