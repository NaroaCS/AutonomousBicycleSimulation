---
sidebar_position: 1
---
import useBaseUrl from '@docusaurus/useBaseUrl';

# Architecture

The core of the simulator is composed of a discrete event-based engine that manages every activity carried out by the agents during their life-cycle using a priority event queue, ordered by time.  The main building blocks of the simulator are the following:

<div style={{textAlign: 'center'}}>
<img src={useBaseUrl('/img/developer/Architecture-1.png')} alt="drawing" width="60%" /> 
</div>

The event-based engine is at the core of the simulator and is fed by events produced by the agents. Any entity that can interact with or produce events is considered to be an agent. 
During the simulation execution, events are handled sequentially, in chronological order. Whenever any agent does an action or takes a decision, it generates and inserts new events into the priority queue.

## Engine
The simulator was implemented from scratch using **[Python 3.7.9](https://docs.python.org/3/reference/)**. An object-oriented paradigm was adopted, where each agent is a class instance.  The engine was developed on top of the  **[SimPy 4.0.1](https://simpy.readthedocs.io/en/latest/simpy_intro/installation.html)** library [1], a process-based discrete-event simulation framework. Under this paradigm, <code> processes</code>  are used to model the behavior of active components, such as bicycles and users. Processes live in an <code>environment</code>  and interact with the environment and with each other via <code>events</code> . The most important event type for our application is the <code>timeout</code> , which allows a process to sleep for the given time, determining the duration of the activity. Events of this type are triggered after a certain amount of simulated time has passed. 

## Infrastructure
The workflow of the simulator is described as follows: initially, Simpy's environment is created, and the provided infrastructure data is used to generate users, bikes, stations, and the road network. Users are introduced into the environment at a given location and departure time, and their task is to move to the specified target location using the defined mode of transportation. The location data is given in terms of longitude and latitude. The characteristics of the bike-sharing system are defined in the <code>bikes</code>  module. If required, station data is also included in its corresponding module. Parameters for users, bikes, and stations are specified in their respective modules. 

## Geospatial data
The geospatial information is provided by the <code>geospatial data</code> module, which contains a) the road graph, b) buildings data, and c) geospatial indexing system. Among these, only the road graph is strictly necessary to perform the simulation. Buildings data is optional, as it is used to generate users' origin and destination locations inside the buildings. This process yields realistic locations and avoids geographical obstacles such as highways or rivers. The geospatial indexing system is also optional, as it is used for the demand prediction and rebalancing manager, explained more in detail in <code>Demand Prediction</code> and <code>Rebalancing</code>. 

Geospatial data was obtained using **[OpenStreetMap](https://www.openstreetmap.org/)** services. Given the bounding box of the city under study, OpenStreetMap <code>highway</code> tag is queried, downloaded, and converted into a directed and weighted graph, denoted as road network from this point onward. 

## Routing Manager
The routing manager is in charge of choosing the most appropriate route (usually the shortest path) to transport people and vehicles around the urban space. This is a critical service and needs to be computed fast and with high resolution to yield results as close to reality. For the task of routing in road networks, an optimized fork **[fork](https://github.com/imartinezl/pandana.git)** of the **[Pandana](http://udst.github.io/pandana/)** Python library was implemented, as it uses contraction hierarchies (CH) to calculate super-fast travel accessibility metrics and shortest paths. The numerical code is in C++. 

:::danger TODO
    Review the link to the fork
:::
 

## Contraction Hierarchies
The contraction hierarchies algorithm is a speed-up technique for finding the shortest path in a graph, and it consists of two phases: preprocessing and query. To achieve its speed-up, CH relies on the fact that road networks do not change frequently. Given a directed, weighted graph $G(V,E,C)$ with vertex set $V$, edge set $E$ and cost function $C: E \rightarrow \mathbb{R}^+$, the goal is to preprocess $G$ in such a way that the subsequent shortest path queries specified by a source node $s$ and a target node $t$ can be answered very quickly. In the preprocessing phase, $G$ is augmented by additional edges $E'$, which are shortcuts that represent the shortest paths in the original graph $G$. In addition, a natural number is assigned to each node $v \in V$, called $level(v)$ [2]. In the query phase, a bidirectional Dijkstra algorithm is applied on the augmented graph $G^\star$. Amongst all nodes settled from the Dijkstra, the one where the added distances from $s$ and to $t$ are minimal determines the shortest path from $s$ to $t$. The query is highly efficient because the modified Dijkstra can discard the majority of the nodes and edges of $G^\star$ while visiting only a small portion of the graph $G^\star$[2].

## Additional modules
The charging manager, the rebalancing manager, and the demand prediction modules will be discussed in greater depth under each mode of transportation. 



**References** 

[1] Matloff, N., 2008. Introduction to discrete-event simulation and the simpy language. Davis, CA. Dept of Computer Science. University of California at Davis. Retrieved on August, 2(2009), pp.1-33.

[2] Geisberger, R., Sanders, P., Schultes, D. and Delling, D., 2008, May. Contraction hierarchies: Faster and simpler hierarchical routing in road networks. In International Workshop on Experimental and Efficient Algorithms (pp. 319-333). Springer, Berlin, Heidelberg.
