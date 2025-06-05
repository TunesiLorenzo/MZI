import gdsfactory as gf
from collections.abc import Sequence
import numpy as np
import os

class MZI_sw:
    def __init__(self, component, wg_w=0.5, arm_l=50, arm_dl=15, 
                 heater_w=3, layer_heater=(11,0), layer_electrical=(12,0),
                 bend_r=8, mmi_l=5, mmi_w=5, mmi_gap=2, mmi_taper_l=5):
        
        self.component = component
        self.wg_w = wg_w
        self.arm_l = arm_l
        self.arm_dl = arm_dl
        self.heater_w = heater_w
        self.layer_heater = layer_heater
        self.layer_electrical = layer_electrical
        self.bend_r = bend_r
        self.mmi_l = mmi_l
        self.mmi_w = mmi_w
        self.mmi_gap = mmi_gap
        self.mmi_taper_l = mmi_taper_l
        self.instance = 1

    def create_structure(self,pos=(0,0)):
        self.pos=pos
        self.instance =+ 1
        self.create_mzi()
        self.route_electrical()


    def create_mzi(self):
        xs_metal = gf.cross_section.heater_metal(width=self.heater_w, layer=self.layer_heater)
        mzi = self.component << gf.components.mzis.mzi2x2_2x2_phase_shifter(length_x=self.arm_l, delta_length=self.arm_dl,
                                                                       straight_x_top=gf.components.straight_heater_metal(length=self.arm_l, cross_section_heater=xs_metal, via_stack=None),
                                                                       splitter=gf.components.mmis.mmi2x2(width_mmi=self.mmi_w,gap_mmi=self.mmi_gap,length_taper=self.mmi_l),
                                                                       combiner=gf.components.mmis.mmi2x2(width_mmi=self.mmi_w,gap_mmi=self.mmi_gap,length_taper=self.mmi_l),
                                                                       bend=gf.components.bends.bend_euler(radius=self.bend_r))
        mzi.move(origin=(0,0),destination=self.pos)
        self.component.add_port(name=f"o_{self.instance}_1",port=mzi["o2"])
        self.component.add_port(name=f"o_{self.instance}_2",port=mzi["o1"])
        self.component.add_port(name=f"o_{self.instance}_3",port=mzi["o3"])
        self.component.add_port(name=f"o_{self.instance}_4",port=mzi["o4"])


    def route_electrical(self):      
        contact = self.component << gf.components.rectangle(size=(self.heater_w,self.heater_w), layer=(12,1))
        contact.dmove(origin=(0,0),destination=(self.mmi_l+2*self.bend_r+self.mmi_taper_l+self.wg_w+self.pos[0],self.mmi_gap+2*self.bend_r+self.pos[1]))
        self.component.add_port(name=f"e_{self.instance}_1",port=contact["e2"])

        contact = self.component << gf.components.rectangle(size=(self.heater_w,self.heater_w), layer=(12,1))
        contact.dmove(origin=(0,0),destination=(self.mmi_l+2*self.bend_r+self.mmi_taper_l+self.arm_l+self.wg_w-self.heater_w+self.pos[0],self.mmi_gap+2*self.bend_r+self.pos[1]))
        self.component.add_port(name=f"e_{self.instance}_2",port=contact["e2"])

master_component=gf.Component("Neuromorphic_Chip")
MZI = MZI_sw(
    component=master_component
)

x_spacing = 0
y_spacing = 70
MZI.create_structure(pos=(x_spacing,0))
MZI.create_structure(pos=(x_spacing,y_spacing))
MZI.create_structure(pos=(x_spacing,2*y_spacing))

x_spacing = 300
MZI.create_structure(pos=(x_spacing,0))
MZI.create_structure(pos=(x_spacing,y_spacing))
MZI.create_structure(pos=(x_spacing,2*y_spacing))

x_spacing = 600
MZI.create_structure(pos=(x_spacing,0))
MZI.create_structure(pos=(x_spacing,y_spacing))
MZI.create_structure(pos=(x_spacing,2*y_spacing))




master_component.pprint_ports()
master_component.draw_ports()
master_component.write_gds(f"mzi_test.gds")


