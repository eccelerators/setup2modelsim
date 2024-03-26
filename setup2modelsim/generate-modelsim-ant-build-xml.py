#******************************************************************************
#
#                  /------o
#            eccelerators
#         o------/
#
# This file is an Eccelerators GmbH sample project.
#
# MIT License:
# Copyright (c) 2023 Eccelerators GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#******************************************************************************

import os
import shutil
import xml.etree.cElementTree as ET
from pathlib import Path
from xml.dom import minidom
from json import loads
from setup_data_to_json import SetupToJson
from io import StringIO

import click

class GenAntBuildXml:
    
    def generate(self, setup_py_file_path='test/setup.py', bustype='axilite', simulation_subdir_path='test/modelsim-axi4lite/build_modelsim_axi4lite.xml'):
        
        target_prefix = 'modelsim-' + bustype +"-"
        time_stamps_prefix = 'simulation/' + 'modelsim-' + bustype +"/work/TimeStamps/"
        simulation_dir_prefix = 'simulation/' + 'modelsim-' + bustype + '/'
        
        # --------------------------
        # extract data from setup.py
        # --------------------------
        extractor = SetupToJson()
        file_path = open(setup_py_file_path, 'r')     
        print("reading {}".format(setup_py_file_path))
        json_string = extractor.extract(setup_py_file_path)
        static_setup_data = loads(json_string)
        
        
        src_data_file_list = []
        for src_data_file_per_dest in static_setup_data["src_data_files"]:                       
            for src_data_file in src_data_file_per_dest[1]:
                src_data_file_list.append(src_data_file)   
         
        tb_data_file_list = []
        for tb_data_file_per_dest in static_setup_data["tb_data_files"]:                       
            for tb_data_file in tb_data_file_per_dest[1]:
                tb_data_file_list.append(tb_data_file) 
                        
        context = {
                "name" : static_setup_data["project_name"],
                "top_entity" : static_setup_data["top_entity"],
                "top_entity_file" : static_setup_data["top_entity_file"], 
                "src_data_file_list" : src_data_file_list,
                "tb_top_entity" : static_setup_data["tb_top_entity"],
                "tb_top_entity_file" : static_setup_data["tb_top_entity_file"],    
                "tb_data_file_list" : tb_data_file_list,
            }  
        
        test_suite_data_dict = {}
        if "test_suites" in static_setup_data:
            for test_suite in static_setup_data["test_suites"]: 
                if "testsuite-indexes" in test_suite:
                    for i in range(int(test_suite["testsuite-indexes"])):
                        test_suite_data_dict["{}_{:d}".format(test_suite["testsuite-name"], i)] = {"file":test_suite["file"], 
                                                                                                   "entry-file":test_suite["entry-file"], 
                                                                                                   "entry-label":test_suite["entry-label"], 
                                                                                                   "index" :str(i)}
                else:
                    test_suite_data_dict[test_suite["testsuite-name"]] = {"file":test_suite["file"], 
                                                                          "entry-file":test_suite["entry-file"], 
                                                                          "entry-label":test_suite["entry-label"]}
        
        test_lab_data_dict = {}
        if "test_labs" in static_setup_data:
            for test_lab in static_setup_data["test_labs"]: 
                test_lab_data_dict[test_lab["testlab-name"]] = {"file":test_lab["file"], 
                                                                  "entry-file":test_lab["entry-file"], 
                                                                  "entry-label":test_lab["entry-label"]}        
        
        simulation_hdl_file_list = src_data_file_list + tb_data_file_list
               
        ordered_hdl_file_dict ={}
        
        for shf in simulation_hdl_file_list:
            if not 'IP-XACT' in shf['file_type']: 
                ordered_hdl_file_dict[shf['hdl_order']] = shf
             
        ordered_hdl_file_dict = dict(sorted(ordered_hdl_file_dict.items()))
    
        
        root = ET.Element("project", name='modelsim-' + bustype)
        
        ET.SubElement(root, "property", name ="vlib-executable", value = "vlib")
        ET.SubElement(root, "property", name ="vmap-executable", value = "vmap")
        ET.SubElement(root, "property", name ="vcom-executable", value = "vcom")
        ET.SubElement(root, "property", name ="vsim-executable", value = "vsim")
                        
        t = ET.SubElement(root, "target", name=target_prefix + "prepare", description="make work folder")
        ET.SubElement(t, "mkdir",  dir=simulation_dir_prefix + "work" )
        ex = ET.SubElement(t, "exec", executable="${vlib-executable}", dir=simulation_dir_prefix + "work", failonerror="true")
        ET.SubElement(ex, "arg", value="${basedir}/" + simulation_dir_prefix + "work" + "/work")
        ex = ET.SubElement(t, "exec", executable="${vmap-executable}", dir=simulation_dir_prefix + "work", failonerror="true")
        ET.SubElement(ex, "arg", value="work")
        ET.SubElement(ex, "arg", value="${basedir}/" + simulation_dir_prefix + "work" + "/work")
        ex = ET.SubElement(t, "exec", executable="${vmap-executable}", dir=simulation_dir_prefix + "work", failonerror="true")
        ET.SubElement(ex, "arg", value="work_lib")
        ET.SubElement(ex, "arg", value="${basedir}/" + simulation_dir_prefix + "work" + "/work")
        
        t = ET.SubElement(root, "target", name=target_prefix + "clean", description="delete work folder")
        dl = ET.SubElement(t, "delete", dir=simulation_dir_prefix + "work")
        dl = ET.SubElement(t, "delete", dir=simulation_dir_prefix + "TimeStamps")

        test_suites_present = False
        if "test_suites" in static_setup_data:
            if len(static_setup_data["test_suites"]) > 0:        
                ET.SubElement(
                    root, "target", 
                    name=target_prefix + "all", description="all from scratch until interactive simulation",
                    depends=" modelsim-" + bustype + "-clean, modelsim-" + bustype + "-prepare, modelsim-" + bustype + "-compile, modelsim-" + bustype + "-simulate-suites")
                test_suites_present = True

        if not test_suites_present:
            ET.SubElement(
                root, "target", 
                name=target_prefix + "all", description="all from scratch until interactive simulation",
                depends=" modelsim-" + bustype + "-clean, modelsim-" + bustype + "-prepare, modelsim-" + bustype + "-compile, modelsim-" + bustype + "-simulate")
          
        ET.SubElement(
            root, "target", 
            name=target_prefix + "all-gui", description="all from scratch until interactive simulation",
            depends=" modelsim-" + bustype + "-clean, modelsim-" + bustype + "-prepare, modelsim-" + bustype + "-compile, modelsim-" + bustype + "-simulate-gui")

        s = ' '
        for kohf, shf in ordered_hdl_file_dict.items():        
            s += '-do_compile_' + target_prefix + shf['file'].replace('/', '_') + ', '
        s = s[:-2]    
        ET.SubElement(root, "target", name = target_prefix + "compile", depends=s, description="compile all")
        
        t = ET.SubElement(root, "target", name=target_prefix + "simulate", description="simulate") 
        ET.SubElement(t, "delete",  dir=simulation_dir_prefix + "../SimulationResults" )
        ET.SubElement(t, "mkdir",  dir=simulation_dir_prefix + "../SimulationResults" )
        echo = ET.SubElement(t, "echo", file=simulation_dir_prefix + "work/simulation.started", append="false")
        echo.text = "STARTED"
        echo = ET.SubElement(t, "echo", file=simulation_dir_prefix + "work/run_all.do", append="false")
        echo.text = "run -all"
        ex = ET.SubElement(t, "exec", executable="${vsim-executable}", dir=simulation_dir_prefix + "work")
        ET.SubElement(ex, "arg",  value="-t")
        ET.SubElement(ex, "arg",  value="ps")
        ET.SubElement(ex, "arg",  value="-L")
        ET.SubElement(ex, "arg",  value="work")
        ET.SubElement(ex, "arg",  value="work." + context['tb_top_entity'] )
        ET.SubElement(ex, "arg",  value="-batch" )
        ET.SubElement(ex, "arg",  value="-gstimulus_path=${basedir}/tb/simstm/")
        ET.SubElement(ex, "arg",  value="-do" )
        ET.SubElement(ex, "arg",  value="run_all.do" )
        echo = ET.SubElement(t, "echo", file=simulation_dir_prefix + "work/simulation.ended", append="false")
        echo.text = "ENDED"        

        t = ET.SubElement(root, "target", name=target_prefix + "simulate-gui", description="simulate start gui")
        ET.SubElement(t, "delete",  dir=simulation_dir_prefix + "../SimulationResults" )
        ET.SubElement(t, "mkdir",  dir=simulation_dir_prefix + "../SimulationResults" )
        ex = ET.SubElement(t, "exec", executable="${vsim-executable}", dir=simulation_dir_prefix + "work")
        ET.SubElement(ex, "arg",  value="-t")
        ET.SubElement(ex, "arg",  value="ps")
        ET.SubElement(ex, "arg",  value="-L")
        ET.SubElement(ex, "arg",  value="work")
        ET.SubElement(ex, "arg",  value="work." + context['tb_top_entity'] )
        ET.SubElement(ex, "arg",  value="-gstimulus_path=${basedir}/tb/simstm/")
        ET.SubElement(ex, "arg",  value="-i" )  
        
        if "test_suites" in static_setup_data:
            if len(static_setup_data["test_suites"]) > 0:
                t = ET.SubElement(root, "target", name=target_prefix + "simulate-suites", description="simulate all suites parallel")
                ET.SubElement(t, "delete",  dir=simulation_dir_prefix + "../SimulationResults" )
                ET.SubElement(t, "mkdir",  dir=simulation_dir_prefix + "../SimulationResults" )
                echo = ET.SubElement(t, "echo", file=simulation_dir_prefix + "../SimulationResults/testSuitesSimulation.start", append="false")
                echo.text = "STARTED"
                echo = ET.SubElement(t, "echo", file=simulation_dir_prefix + "work/run_all.do", append="false")
                echo.text = "run -all"
                prl = ET.SubElement(t, "parallel", threadCount="8")
              
                for test_suite, test_suite_data in test_suite_data_dict.items():   
                    ex = ET.SubElement(prl, "exec", executable="${vsim-executable}", dir=simulation_dir_prefix + "work")
                    ET.SubElement(ex, "redirector", 
                                  output=simulation_dir_prefix + "../SimulationResults/" + test_suite + ".out", 
                                  error=simulation_dir_prefix + "../SimulationResults/" + test_suite + ".err",
                                  alwayslog="true")
                    
                    ET.SubElement(ex, "arg",  value="-t")
                    ET.SubElement(ex, "arg",  value="ps")
                    ET.SubElement(ex, "arg",  value="-L")
                    ET.SubElement(ex, "arg",  value="work")
                    ET.SubElement(ex, "arg",  value="work." + context['tb_top_entity'] )
                    ET.SubElement(ex, "arg",  value="-batch" )
                    ET.SubElement(ex, "arg",  value="-gstimulus_path=${basedir}/tb/simstm/")
                    ET.SubElement(ex, "arg",  value="-gstimulus_file=" + test_suite_data["entry-file"])
                    ET.SubElement(ex, "arg",  value="-gstimulus_main_entry_label=" + test_suite_data["entry-label"])
                    if  "index" in test_suite_data:
                        ET.SubElement(ex, "arg",  value="-gstimulus_test_suite_index=" + test_suite_data["index"])
                    ET.SubElement(ex, "arg",  value="-do" )
                    ET.SubElement(ex, "arg",  value="run_all.do" )
                echo = ET.SubElement(t, "echo", file=simulation_dir_prefix + "../SimulationResults/testSuitesSimulation.end", append="false")
                echo.text = "ENDED" 
                
                ex = ET.SubElement(t, "exec", executable="${python-executable}")
                ET.SubElement(ex, "arg",  value="submodules/collect_fpga_build_results/collect_fpga_build_results/collect-simulation-results.py")
                ET.SubElement(ex, "arg",  value="--infile")
                ET.SubElement(ex, "arg",  value="setup.py")
                ET.SubElement(ex, "arg",  value="--inoutdir_simulation_results_dir_path")
                ET.SubElement(ex, "arg",  value="simulation/SimulationResults")        
                
                ET.SubElement(t, "available", file="simulation/SimulationResults/testSuitesSimulation.xml", property="testSuitesSimulation.xml.present")
                ET.SubElement(t, "antcall", target=target_prefix + "do-remove-junit-artifacts")
                ET.SubElement(t, "antcall", target=target_prefix + "complain-about-junit-artifacts")
    
                t = ET.SubElement(root, "target", {"name":target_prefix + "do-remove-junit-artifacts", "if":"testSuitesSimulation.xml.present"})           
                dl = ET.SubElement(t, "delete", failonerror="false", includeemptydirs="true")
                fs = ET.SubElement(dl, "fileset", dir="simulation/SimulationResults")
                ET.SubElement(fs, "include",name="**/*")
                ET.SubElement(fs, "exclude",name="**/testSuitesSimulation.xml")
     
                t = ET.SubElement(root, "target", {"name":target_prefix + "complain-about-junit-artifacts", "unless":"testSuitesSimulation.xml.present"})
                ET.SubElement(t, "echo", message="testSuitesSimulation.xml couldn't be build from artifacts, keeping artifacts")        
            
        if "test_labs" in static_setup_data:         
            for test_lab, test_lab_data in test_lab_data_dict.items():   
                t = ET.SubElement(root, "target", name=target_prefix + "simulate-" + test_lab, description="run simulation") 
                ET.SubElement(t, "delete",  dir=simulation_dir_prefix + "../SimulationResults" )
                echo = ET.SubElement(t, "echo", file=simulation_dir_prefix + "work/simulation.started", append="false")
                echo.text = "STARTED"
                echo = ET.SubElement(t, "echo", file=simulation_dir_prefix + "work/run_all.do", append="false")
                echo.text = "run -all"
                ex = ET.SubElement(t, "exec", executable="${vsim-executable}", dir=simulation_dir_prefix + "work")                             
                ET.SubElement(ex, "arg",  value="-t")
                ET.SubElement(ex, "arg",  value="ps")
                ET.SubElement(ex, "arg",  value="-L")
                ET.SubElement(ex, "arg",  value="work")
                ET.SubElement(ex, "arg",  value="work." + context['tb_top_entity'] )
                ET.SubElement(ex, "arg",  value="-batch" )
                ET.SubElement(ex, "arg",  value="-gstimulus_path=${basedir}/tb/simstm/")
                ET.SubElement(ex, "arg",  value="-gstimulus_file=" + test_lab_data["entry-file"])
                ET.SubElement(ex, "arg",  value="-gstimulus_main_entry_label=" + test_lab_data["entry-label"])
                ET.SubElement(ex, "arg",  value="-do" )
                ET.SubElement(ex, "arg",  value="run_all.do" )                               
                echo = ET.SubElement(t, "echo", file=simulation_dir_prefix + "work/simulation.ended", append="false")
                echo.text = "ENDED"
                
                t = ET.SubElement(root, "target", name=target_prefix + "simulate-gui-" + test_lab, description="simulate and write trace.vcd")
                ET.SubElement(t, "delete",  dir=simulation_dir_prefix + "../SimulationResults" )
                echo = ET.SubElement(t, "echo", file=simulation_dir_prefix + "work/simulation.started", append="false")
                echo.text = "STARTED"
                echo = ET.SubElement(t, "echo", file=simulation_dir_prefix + "work/run_all.do", append="false")
                echo.text = "run -all"
                ex = ET.SubElement(t, "exec", executable="${vsim-executable}", dir=simulation_dir_prefix + "work")                  
                ET.SubElement(ex, "arg",  value="-t")
                ET.SubElement(ex, "arg",  value="ps")
                ET.SubElement(ex, "arg",  value="-L")
                ET.SubElement(ex, "arg",  value="work")
                ET.SubElement(ex, "arg",  value="work." + context['tb_top_entity'] )
                ET.SubElement(ex, "arg",  value="-gstimulus_path=${basedir}/tb/simstm/")
                ET.SubElement(ex, "arg",  value="-gstimulus_file=" + test_lab_data["entry-file"])
                ET.SubElement(ex, "arg",  value="-gstimulus_main_entry_label=" + test_lab_data["entry-label"])
                ET.SubElement(ex, "arg",  value="-i" )   
                echo = ET.SubElement(t, "echo", file=simulation_dir_prefix + "work/simulation.ended", append="false")
                echo.text = "ENDED"                                   
            
                
        t = ET.SubElement(root, "target", name=target_prefix + "init-skip-properties")
        ET.SubElement(t, "mkdir",  dir=time_stamps_prefix[:-1] )
        for kohf, shf in ordered_hdl_file_dict.items():     
            ET.SubElement(t, "uptodate",  srcfile="${basedir}/" + shf['file'],  targetfile="${basedir}/" + time_stamps_prefix + shf['file'].replace('/', '_'),  property=target_prefix + shf['file'].replace('/', '_') + '.skip',  value="true" )        
         
        for kohf, shf in ordered_hdl_file_dict.items():
            do = '-do_compile_' + target_prefix + shf['file'].replace('/', '_')
            if shf['file_type'] == 'Verilog':
                t = ET.SubElement(root, "target", name=do, depends=target_prefix + "init-skip-properties", unless=target_prefix + shf['file'].replace('/', '_') + '.skip')    
                ex = ET.SubElement(t, "exec", executable="${vcom-executable}", dir=simulation_dir_prefix + "work", failonerror="true")
                ET.SubElement(ex, "arg", value="${basedir}/" + shf['file'])       
            else:
                t = ET.SubElement(root, "target", name=do, depends=target_prefix + "init-skip-properties", unless=target_prefix + shf['file'].replace('/', '_') + '.skip')      
                ex = ET.SubElement(t, "exec", executable="${vcom-executable}", dir=simulation_dir_prefix + "work", failonerror="true")
                if '2008' in shf['file_type']:
                    ET.SubElement(ex, "arg", value="-2008")
                ET.SubElement(ex, "arg", value="${basedir}/" + shf['file'])
            ET.SubElement(t, "touch", file="${basedir}/" + time_stamps_prefix + shf['file'].replace('/', '_'))   
                                   
        tree = ET.ElementTree(root)
        
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="   ")            
        xml_file = StringIO(xml_str)
        xml_lines = xml_file.readlines()
            
        xml_lines_beautified = []
        for l in xml_lines:
            if target_prefix + "compile"  in l or target_prefix + "all" in l:
                l = l.replace('depends="', 'depends="\n    ')
                l = l.replace(',', ',\n    ')
                l = l.replace(' description="', '\n         description="')
            if 'property name="vlib-executable"' in l:
                xml_lines_beautified.append('   <!-- may be overridden in main build script -->\n')
            if '<target' in l:
                xml_lines_beautified.append('\n')
            xml_lines_beautified.append(l)
                            
        bf = simulation_subdir_path + '/build-' + target_prefix[:-1] + '.xml'
        if os.path.exists(bf):
            os.remove(bf)      
            
        print("writing {}".format(bf))  
        with open(bf, "w") as f:
            for l in xml_lines_beautified:
                f.write(l)                  


@click.command()
@click.option('--infile', default='../../../setup.py',  help='setup_py_file_path')
@click.option('--inbustype', type=click.Choice(['axi4lite', 'avalon', 'wishbone']), default='axi4lite',  help='bustype')
@click.option('--outdir_simulation_subdir', default='../../../simulation/modelsim-axi4lite',  help='simulation_subdir_path')
def generate(infile, inbustype, outdir_simulation_subdir):
    obj = GenAntBuildXml()
    obj. generate(setup_py_file_path = infile, 
                  bustype = inbustype,
                  simulation_subdir_path = outdir_simulation_subdir
                  )
              

if __name__ == '__main__':
    generate()
