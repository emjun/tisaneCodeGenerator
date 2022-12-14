"""
Tests that the constructed statistical model generates a Python script correctly. 
"""
from tisanecodegenerator.statisticalModel import StatisticalModel
from tisanecodegenerator.codeGeneratorStrings import CodeGeneratorStrings
from tisanecodegenerator.codeGenerator import CodeGenerator

# import pandas as pd
import os
from pathlib import Path
from typing import Dict, Set
# import filecmp
# from difflib import Differ
import ast
import unittest

test_data_repo_name = "input_json/"
test_script_repo_name = "key_scripts/"
test_generated_script_repo_name = "generated_scripts/"
dir = os.path.dirname(__file__)
data_dir = os.path.join(dir, test_data_repo_name)
script_dir = os.path.join(dir, test_script_repo_name)
generated_script_dir = os.path.join(dir, test_generated_script_repo_name)
# df = pd.read_csv(os.path.join(dir, "pigs.csv"))

### Import helper functions
from helpers import *

class GenerateCodeTest(unittest.TestCase):
    def test_code_generator_creation(self): 
        filenames = ["main_only.json", "main_interaction.json"]
        
        for fn in filenames: 
            filepath = os.path.join(data_dir, fn)

            sm = construct_statistical_model(filepath)        
            data = Path('data.csv')
            cg = CodeGenerator(sm, data) # Provide data
            self.assertIsInstance(cg.dataPath, os.PathLike)
            self.assertEqual(cg.dataPath, data)
            self.assertRaises(ValueError, CodeGenerator.__init__, cg, sm, Path('data.txt'))

            ## Main and Interaction effects
            filename = "main_interaction.json"
            filepath = os.path.join(data_dir, filename)

            sm = construct_statistical_model(filepath)        
            data = Path('data.csv')
            cg = CodeGenerator(sm, data) # Provide data
            self.assertIsInstance(cg.dataPath, os.PathLike)
            self.assertEqual(cg.dataPath, data)
            self.assertRaises(ValueError, CodeGenerator.__init__, cg, sm, Path('data.txt'))

    def test_load_strings(self): 
        cg_strings = CodeGeneratorStrings()

        self.assertIsInstance(cg_strings, CodeGeneratorStrings)
        data = cg_strings.data
        self.assertIsInstance(data, dict)
        self.assertIn("installs", data.keys())
        self.assertIn("imports", data.keys())

    def test_preamble(self):
        filenames = ["main_only.json", "main_interaction.json"]

        for fn in filenames: 
            filepath = os.path.join(data_dir, fn)

            sm = construct_statistical_model(filepath)        
            cg = CodeGenerator(sm)
            self.assertIs(sm, cg.statisticalModel)

            # Compare code snippets
            preamble = cg.preamble()
            self.assertIn("install.packages('tidyverse')", preamble)
            self.assertIn("install.packages('lme4'", preamble)
            self.assertIn("library(tidyverse)", preamble)
            self.assertIn("library(lme4)", preamble)

            ## Main and Interaction effects
            filename = "main_interaction.json"
            filepath = os.path.join(data_dir, filename)

            sm = construct_statistical_model(filepath)        
            cg = CodeGenerator(sm)
            self.assertIs(sm, cg.statisticalModel)

            # Compare code snippets
            preamble = cg.preamble()
            self.assertIn("install.packages('tidyverse')", preamble)
            self.assertIn("install.packages('lme4'", preamble)
            self.assertIn("library(tidyverse)", preamble)
            self.assertIn("library(lme4)", preamble)
    
    def test_loading(self): 
        filenames = ["main_only.json", "main_interaction.json"]
    
        for fn in filenames: 
            filepath = os.path.join(data_dir, fn)

            sm = construct_statistical_model(filepath)       

            # Compare code snippets
            cg = CodeGenerator(sm) # No data
            self.assertIs(sm, cg.statisticalModel)
            loading = cg.loading()
            # Check that comment to add data path is included
            self.assertIn("# Replace 'PATH'", loading)
            self.assertIn("data <- read.csv('PATH')", loading)
            
            cg = CodeGenerator(sm, 'data.csv') # Provide data
            self.assertIs(sm, cg.statisticalModel)
            loading = cg.loading()
            self.assertIn("data <- read.csv('data.csv')", loading)


    def test_modeling(self): 
        ## Main effects only
        filename = "main_only.json"
        filepath = os.path.join(data_dir, filename)

        sm = construct_statistical_model(filepath)       

        # Compare code snippets
        cg = CodeGenerator(sm) # No data
        self.assertIs(sm, cg.statisticalModel)
        modeling = cg.modeling()

        # Check the formula
        formula = extract_formula(modeling)
        dv = formula.split("~")[0]
        ivs = formula.split("~")[1]
        ivs = ivs.split("+")
        self.assertEqual("PINCP", dv) # DV
        self.assertIn("AGEP", ivs) # IVs
        self.assertIn("SCHL", ivs)

        # Check family function
        family = extract_family(modeling)
        self.assertEqual("gaussian", family)
        
        # Check link function
        link = extract_link(modeling)
        self.assertEqual("'identity'", link)
        
        # Check data
        data = extract_data(modeling)
        self.assertIn("data", data) # Data

        ## Main and Interaction effects
        filename = "main_interaction.json"
        filepath = os.path.join(data_dir, filename)

        sm = construct_statistical_model(filepath)       

        # Compare code snippets
        cg = CodeGenerator(sm) # No data
        self.assertIs(sm, cg.statisticalModel)
        modeling = cg.modeling()

        # Check the formula
        formula = extract_formula(modeling)
        dv = formula.split("~")[0]
        ivs = formula.split("~")[1]
        ivs = ivs.split("+")
        self.assertEqual("Y", dv) # DV
        self.assertIn("X1", ivs) # IVs
        self.assertIn("X2", ivs)
        self.assertIn("X1_X_X2", ivs)

        # Check family function
        family = extract_family(modeling)
        self.assertEqual("gaussian", family)
        
        # Check link function
        link = extract_link(modeling)
        self.assertEqual("'identity'", link)
        
        # Check data
        data = extract_data(modeling)
        self.assertIn("data", data) # Data

    def test_write_out_file(self): 
        filenames = ["main_only.json", "main_interaction.json"]
    
        for fn in filenames: 
            filepath = os.path.join(data_dir, fn)

            sm = construct_statistical_model(filepath)        
            cg = CodeGenerator(sm)
            generated_script_path = cg.write_out_file(path=generated_script_dir)
            
            # Make sure the generated and output script runs
            # Not necessary to make sure that the script is identical to another key script, just that the script is valid and executable, even if a Path is missing
            import subprocess
            res = subprocess.run(f"Rscript {generated_script_path}", shell=True)
            self.assertGreaterEqual(res.returncode, 0)