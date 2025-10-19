# Abstract Syntax Tree Implementation for Automatic Generation of Building Energy Simulation Code

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
## 📖 Introduction
This repository contains the implementation code for building energy simulation programs based on Abstract Syntax Tree (AST), along with related research papers. The project enables automatic generation of building energy simulation code through natural language processing and template-based approaches.
## 📝 Publication
This code accompanies our research paper.
```bash
Title:《Automatic Code Generation Method for Building a Co-Simulation Platform Integrating Building Automatic Systems and EnergyPlus》
Author: Chenxi Guo, Hairong Yan, Chuang Chen, 
Journal: Energy & Buildings
```
## 📁 Project Structure
```bash
Abstract-syntax-tree-implementation-for-automatic-generation-of-building-energy-simulation-code/main/
├── 📁 Experts/ # Expert manually constructed code
│ ├── MG1.py # Manual Generation 1
│ ├── MG2.py # Manual Generation 2
│ ├── MG3.py # Manual Generation 3
│ └── MG4.py # Manual Generation 
├── 📁 auto-generate/ # Automated generation experimental code (Proposed Method)
│ ├── G1Exp1.py # Generated Experiment 1
│ ├── G1Exp2.py # Generated Experiment 2
│ ├── G1Exp3.py # Generated Experiment 3
│ └── G1Exp4.py # Generated Experiment 4
├── 📁 example/ # Quick Start Example
│ ├── app.py # Example application main program
│ ├── sample_dataset.csv # Sample dataset
│ └── README.md # Example-specific instructions
└── 📄 README.md (This file)
```
## 🚀 Quick Start
We provide a simple example to help you quickly understand the core workflow of our proposed method.
### 1.Prerequisites
- Python 3.8 or higher
- Required dependencies (install via pip):

```bash
pip install requests flask numpy pandas scikit-learn
cd example
```
### 2.Prerequisites


