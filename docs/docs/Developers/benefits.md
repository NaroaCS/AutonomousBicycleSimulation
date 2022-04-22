---
sidebar_position: 6
---
import useBaseUrl from '@docusaurus/useBaseUrl';

# Benefits and performance 

## Simulator benefits
The proposed simulation framework is highly configurable and flexible, with many parameters at different levels: geospatial data, user behavior, bike features, charging, and rebalancing strategies, among others. At the moment, it includes tstation-based, dockless, and autonomous bike-sharing systems, but other mobility modes can be integrated with little effort. It can also combine multiple modes of transportation simultaneously, allowing researchers to test the effects of various mode choice models. Furthermore, it can be easily transferred to other cities by just changing the OpenStreepMap query. In this sense, the simulator works with geospatial data of high resolution and precision. The simulation framework is able to perform and scale linearly with respect to the number of trips and to the number of bikes. On the contrary to the use of MATSim, the simulation time is not restricted to one day. In fact, its performance allows to simulate a week of data in few minutes.

## Performance 
In terms of performance, the simulator takes around 80 seconds to compute a station-based bike-sharing system run with 70000 bike trips (that elapse seven days of real data). In the case of the dockless system, this time increases up to 205 seconds due to the larger fleet size and the creation of KD-trees for closest bike queries every time a trip is requested. Regarding the autonomous system, it takes around 60 seconds to compute a run, given its reduced fleet size.These experiments were run with Python 3.7.4 in a Ubuntu 18.04 Linux system with an Intel i5-9400F processor with 6 threads running at 2.90 GHz using 64 GB of RAM. Even though these time-benchmarks are very satisfactory to run multiple simulations, perform sensitivity analysis and study the parameters' influence, we believe it could be further improved by integrating the event-based engine with a low-level programming interface. 