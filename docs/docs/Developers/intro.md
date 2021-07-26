---
sidebar_position: 1
---
import useBaseUrl from '@docusaurus/useBaseUrl';

# Architecture

The core of the simulator is composed of a discrete event-based engine that manages every activity carried out by the agents during their life-cycle using a priority event queue, ordered by time.  The main building blocks of the simulator are the following: 
<img src={useBaseUrl('/img/developer/Architecture-1.png')} alt="drawing" width="60%" /> 

The event-based engine is at the core of the simulator and is fed by events produced by the agents. Any entity that can interact with or produce events is considered to be an agent. 
During the simulation execution, events are handled sequentially, in chronological order. Whenever any agent does an action or takes a decision, it generates and inserts new events into the priority queue.

Let $f:[a,b] \to \R$ be Riemann integrable. Let $F:[a,b]\to\R$ be $F(x)=
\int_{a}^{x}f(t)dt$. Then $$F$$ is continuous, and at all $x$ such that $f$ is continuous at $x$, $F$ is differentiable at $x$ with $F'(x)=f(x)$.




