# monkeys
[![PyPI version](https://badge.fury.io/py/monkeys.svg)](https://badge.fury.io/py/monkeys)
![Liberapay receiving](https://img.shields.io/liberapay/receives/hchasestevens.svg)

> "If an army of monkeys were strumming on typewriters they might write all the books in the British Museum."

`monkeys` is a framework designed to make genetic programming in Python accessible, quick, flexible, and fun.

[**Get started here**](examples/notebooks/Getting%20started%20with%20monkeys.ipynb).


## What is genetic programming?

Genetic programming algorithms are a class of evolutionary algorithms in which solutions to a problem are represented as executable tree 
structures - programs. In order to use genetic programming in order to solve a problem, two things must be specified:

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
specify how your programs should be structured. 

`monkeys` supports Python 2.7 and 3.x.


## Examples 

### Tutorials:
- [**Getting started with monkeys**](examples/notebooks/Getting%20started%20with%20monkeys.ipynb): An introduction to the `monkeys` framework, which outlines the type system. 
- [**Monkeys in abstract syntax trees**](examples/notebooks/Monkeys%20in%20abstract%20syntax%20trees.ipynb): using `monkeys` to generate Python code directly.
- [**Debugging with monkeys**](examples/notebooks/Debugging%20with%20monkeys.ipynb): A guide for discovering and diagnosing bugs in your codebase with `monkeys`.

### Sample usages:
- [**Linting by example**](examples/notebooks/Linting%20by%20example.ipynb): Generating linting rules by supplying positive/negative code examples.
- [**Solving logic puzzles with monkeys**](examples/notebooks/Solving%20logic%20puzzles%20with%20monkeys.ipynb): Solving logic puzzles using the `monkeys` diagnostic tool.
- More to come!


## Contacts

* Name: [H. Chase Stevens](http://www.chasestevens.com)
* Twitter: [@hchasestevens](https://twitter.com/hchasestevens)
