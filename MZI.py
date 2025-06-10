import gdsfactory as gf
from collections.abc import Sequence
import numpy as np
import os

class MZI_sw:
    def __init__(self, component, wg_w=0.5, arm_l=50, arm_dl=15, layer_wg=(1,0),
                 heater_w=3, layer_heater=(11,0), layer_electrical=(12,0),
                 bend_r=8, mmi_l=5, mmi_w=5, mmi_gap=2, mmi_taper_l=2):
        
        self.component = component
        self.wg_w = wg_w
        self.layer_wg = layer_wg
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
        self.create_mzi()
        self.instance += 1
        self.route_electrical()


    def create_mzi(self):
        xs_metal = gf.cross_section.heater_metal(width=self.heater_w, layer=self.layer_heater)
        mzi = self.component << gf.components.mzis.mzi2x2_2x2_phase_shifter(length_x=self.arm_l, delta_length=self.arm_dl,
                                                                       straight_x_top=gf.components.straight_heater_metal(length=self.arm_l, cross_section_heater=xs_metal, via_stack=None),
                                                                       splitter=gf.components.mmis.mmi2x2(width_mmi=self.mmi_w,gap_mmi=self.mmi_gap,length_taper=self.mmi_taper_l,length_mmi=self.mmi_l),
                                                                       combiner=gf.components.mmis.mmi2x2(width_mmi=self.mmi_w,gap_mmi=self.mmi_gap,length_taper=self.mmi_taper_l,length_mmi=self.mmi_l),
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


    def add_grating_coupler(self, pos=[[0,140],[1400,140]], fiberarray_spacing=100, fiberarray_clearance=50):

        gdspath = os.path.join(os.getcwd(), "ANT_GC.GDS")
        antgc = gf.read.import_gds(gdspath)

        my_route_s = gf.cross_section.strip(
            width=self.wg_w,                # same as route_width=5
            layer=self.layer_wg           # same as your original routing_layer usage
        )

        antgc.add_port(
            "o1",
            center=(antgc.x, antgc.y - 19.95),
            orientation=270,
            cross_section=my_route_s
            )

        grating_number = 3
        for idx in range(2):
            for i in range(grating_number):
                antgc_ref = self.component << antgc.copy()
                
                antgc_ref.dmove(   # con dmove puoi spostare nel punto desiderato al posto che move "relativo"
                origin=(antgc_ref.x, antgc_ref.y), # .x e .y ritornano il centro del componente
                destination=(pos[idx][0]+((2*idx-1)*fiberarray_clearance),pos[idx][1]-(70*i)))
                antgc_ref.drotate(angle=90+(idx*180), center=antgc_ref.center)

                shadow_rect = self.component << gf.components.rectangle(size=(0.5, 0.5), layer=self.layer_wg, port_type="optical") # needed because add port is broken as of 9.7.0
                shadow_rect.connect("o3", antgc_ref["o1"]),
                self.component.add_port(f"Grating{idx}_{i}", port=shadow_rect["o1"])

    

    def interconnect_custom(self):

        crossing_only = gf.components.waveguides.crossing_etched()
        crossing_function = gf.components.waveguides.crossing45(crossing=crossing_only, port_spacing=20)
        
        # crossing_function = gf.components.waveguides.crossing_etched()

        my_route_s = gf.cross_section.strip(
            width=self.wg_w,                # same as route_width=5
            layer=self.layer_wg,           # same as your original routing_layer usage
            radius_min=1
        )


        c1 = self.component << crossing_function.copy()
        c1.dmove(origin=(c1.x, c1.y), destination=(350,40))

        c2 = self.component << crossing_function.copy()
        c2.dmove(origin=(c2.x, c2.y), destination=(440,65))

        c3 = self.component << crossing_function.copy()
        c3.dmove(origin=(c3.x, c3.y), destination=(370,100))

        aux1 = self.component << gf.components.rectangle(size=(1.5*self.arm_l, self.wg_w),layer=self.layer_wg,port_type="optical")
        aux1.dmove(origin=(aux1.x,aux1.y),destination=(670,-40))

        gf.routing.route_bundle_sbend(component=self.component,
            ports2=[self.component["o_1_4"],self.component["o_1_3"],self.component["o_2_4"], self.component["o_2_3"],self.component["o_3_4"],self.component["o_6_1"],self.component["o_6_2"], c2["o4"], 
                    self.component["o_5_1"],c1["o3"],self.component["o_4_1"],self.component["o_4_2"]],
            ports1=[aux1["o1"], c1["o2"],c1["o4"],c3["o2"],c3["o4"],self.component["o_3_3"],c3["o3"], c3["o1"], c2["o3"],c2["o2"],c2["o1"],c1["o1"]],
            cross_section=my_route_s)
        

        c4 = self.component << crossing_function.copy()
        c4.dmove(origin=(c4.x, c4.y), destination=(930,100))

        gf.routing.route_bundle_sbend(component=self.component,
            ports2=[self.component["o_9_1"],self.component["o_6_4"],self.component["o_5_3"],self.component["o_8_2"],self.component["o_7_1"],aux1["o3"],c4["o3"],c4["o1"]],
            ports1=[self.component["o_6_3"],c4["o4"],c4["o2"],self.component["o_5_4"],self.component["o_4_3"],self.component["o_7_2"],self.component["o_9_2"],self.component["o_8_1"]],
            cross_section=my_route_s)
        
        gf.routing.route_bundle_sbend(component=self.component,
            ports2=[self.component["o_3_1"],self.component["o_2_1"],self.component["o_1_2"]],
            ports1=[self.component["Grating0_0"],self.component["Grating0_1"],self.component["Grating0_2"]],
            cross_section=my_route_s)
        
        gf.routing.route_bundle_sbend(component=self.component,
            ports2=[self.component["o_7_4"],self.component["o_8_3"],self.component["o_9_3"]],
            ports1=[self.component["Grating1_2"],self.component["Grating1_1"],self.component["Grating1_0"]],
            cross_section=my_route_s)

master_component=gf.Component("Neuromorphic_Chip")
MZI = MZI_sw(
    component=master_component,
    arm_l=150,
    mmi_l=45,
    mmi_w=6,
    mmi_gap=1.5,
    arm_dl=0,
)

device_l=220

x_spacing = 0
y_spacing = 70
MZI.create_structure(pos=(x_spacing,0))
MZI.create_structure(pos=(x_spacing,y_spacing))
MZI.create_structure(pos=(x_spacing,2*y_spacing))

x_spacing = 300 + device_l
MZI.create_structure(pos=(x_spacing,0))
MZI.create_structure(pos=(x_spacing,y_spacing))
MZI.create_structure(pos=(x_spacing,2*y_spacing))

x_spacing = 600 + 2 * device_l
MZI.create_structure(pos=(x_spacing,0))
MZI.create_structure(pos=(x_spacing,y_spacing))
MZI.create_structure(pos=(x_spacing,2*y_spacing))

MZI.add_grating_coupler()

MZI.interconnect_custom()

master_component.pprint_ports()
master_component.draw_ports()
master_component.write_gds(f"mzi_test.gds")


