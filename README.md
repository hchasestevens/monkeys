# monkeys
> "If an army of monkeys were strumming on typewriters they might write all the books in the British Museum."

`monkeys` is a framework designed to make genetic programming in Python accessible, quick, and flexible.


## What is genetic programming?

Genetic programming algorithms are a class of evolutionary algorithms in which solutions to a problem are represented as executable tree 
structures - programs. In order two use genetic programming in order to solve a problem, two things must be specified:

1. What form(s) a potential solution can take.

2. A method of scoring solutions based on their meritoriousness.

Given these, a genetic programming system can perform intelligent exploration and search through the space of potential solutions, 
narrowing in on those programs that best solve the problem as specified. Genetic programming has achieved human-competitive 
results in a wide swath of domains, including:

- Satellite [antenna design](https://ti.arc.nasa.gov/m/pub-archive/1244h/1244%20(Hornby).pdf) for NASA
- The creation of novel [quantum computing algorithms](http://faculty.hampshire.edu/lspector/pubs/GP-quantum-GP98-with-cite.pdf)
- Evolving [game AI](https://cs.gmu.edu/~sean/papers/robocupShort.pdf)
- The [automatic repair](http://dijkstra.cs.virginia.edu/genprog/papers/weimer-icse2012-genprog-preprint.pdf) of buggy code.


## monkeys to the rescue!

> "Ford, there's an infinite number of monkeys outside who want to talk to us about this script for Hamlet they've worked out."

`monkeys` makes getting started with genetic programming painless and fun. Install `monkeys` by running:

```
pip install monkeys
```

`monkeys` uses a variant of genetic programming called "strongly-typed genetic programming" in order to allow you to quickly and easily
specify how your programs should be structured. An introduction to the `monkeys` framework is given in "Getting started with monkeys"\*, 
which outlines the type system. `monkeys` can also be used to generate Python code directly, see "Monkeys in abstract syntax trees"\*. 
A guide for discovering and diagnosing bugs in your codebase with `monkeys` can be found in [Debugging with monkeys](examples/notebooks/Debugging%20with%20monkeys.ipynb).

\* Coming shortly.


## Contacts

* Name: [H. Chase Stevens](http://www.chasestevens.com)
* Twitter: [@hchasestevens](https://twitter.com/hchasestevens)
