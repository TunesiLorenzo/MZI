import gdsfactory as gf
from collections.abc import Sequence
import numpy as np
import os

class MZI_sw:
    def __init__(self, component, wg_w=0.5, arm_l=50, arm_dl=15, layer_wg=(1,0),
                 heater_w=3, layer_heater=(11,0), layer_electrical=(12,0),
                 bend_r=8, mmi_l=5, mmi_w=5, mmi_gap=2, mmi_taper_l=2, mmi_taper_w=1.53,
                 num_pads=10, pad_size=76, pad_tolerance=2, pad_spacing=100, pad_clearance=800, 
                 grating_number=8, fiberarray_spacing=127, fiberarray_clearance=100,
                 thermal_trench=True, length_y=15
                 ):
        
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
        self.mmi_taper_w = mmi_taper_w
        self.instance = 1


        self.num_pads = num_pads
        self.pad_size = pad_size
        self.pad_tolerance = pad_tolerance
        self.pad_spacing = pad_spacing
        self.pad_clearance = pad_clearance

        self.grating_number=grating_number
        self.fiberarray_spacing=fiberarray_spacing
        self.fiberarray_clearance=fiberarray_clearance
        
        self.thermal_trench = thermal_trench
        self.length_y = length_y

    def create_structure(self,pos=(0,0)):
        self.pos=pos
        self.create_mzi()
        self.route_electrical()
        self.instance += 1


    def create_mzi(self):
        xs_metal = gf.cross_section.heater_metal(width=self.heater_w, layer=self.layer_heater)
        xs_metal2 = gf.cross_section.strip(width=self.wg_w, layer=self.layer_heater)
        xs_silicon = gf.cross_section.strip(width=self.wg_w, layer=self.layer_wg)
        xs_strip_metal = gf.cross_section.strip_heater_metal(width=self.wg_w, layer=self.layer_wg,heater_width=self.heater_w,layer_heater=self.layer_heater)

        mzi = self.component << gf.components.mzis.mzi2x2_2x2_phase_shifter(length_x=self.arm_l, delta_length=self.arm_dl, cross_section=xs_silicon, length_y=self.length_y,
                                                                       straight_x_top=gf.components.straight_heater_metal_simple(length=self.arm_l, 
                                                                                                                          cross_section_waveguide_heater=xs_strip_metal,
                                                                                                                          cross_section_heater=xs_metal, 
                                                                                                                          via_stack=None),
                                                                       splitter=gf.components.mmis.mmi2x2(width=self.wg_w,width_mmi=self.mmi_w,gap_mmi=self.mmi_gap,length_taper=self.mmi_taper_l,length_mmi=self.mmi_l,width_taper=self.mmi_taper_w),
                                                                       combiner=gf.components.mmis.mmi2x2(width=self.wg_w,width_mmi=self.mmi_w,gap_mmi=self.mmi_gap,length_taper=self.mmi_taper_l,length_mmi=self.mmi_l),
                                                                       bend=gf.components.bends.bend_euler(width=self.wg_w,radius=self.bend_r))
        if self.thermal_trench:
            thermal_t = self.component << gf.components.rectangle(size=(self.arm_l-20,20),layer=(203,0))
            thermal_t.move(origin=(0,0),destination=(self.pos[0]+self.mmi_l+self.mmi_taper_l+2*self.bend_r+10,self.pos[1]-12))
        mzi.move(origin=(0,0),destination=self.pos)
        self.component.add_port(name=f"o_{self.instance}_1",port=mzi["o2"])
        self.component.add_port(name=f"o_{self.instance}_2",port=mzi["o1"])
        self.component.add_port(name=f"o_{self.instance}_3",port=mzi["o3"])
        self.component.add_port(name=f"o_{self.instance}_4",port=mzi["o4"])


    def route_electrical(self):      
        contact = self.component << gf.components.rectangle(size=(10,15), layer=(12,0))
        contact.dmove(origin=(0,0),destination=(self.mmi_l+2*self.bend_r+self.mmi_taper_l+self.pos[0],
                                                self.mmi_gap/2+self.mmi_taper_w/2+2*self.bend_r+self.pos[1]+self.length_y-15/2))
        
        self.component.add_port(name=f"e_{self.instance}_1",port=contact["e1"])

        contact = self.component << gf.components.rectangle(size=(10,15), layer=(12,0))
        contact.dmove(origin=(0,0),destination=(self.mmi_l+2*self.bend_r+self.mmi_taper_l+self.arm_l-10+self.pos[0],
                                                self.mmi_gap/2+self.mmi_taper_w/2+2*self.bend_r+self.pos[1]+self.length_y-15/2))
        self.component.add_port(name=f"e_{self.instance}_2",port=contact["e3"])

    def add_pads(self):
        pad_array_in = self.component << gf.components.pad_array("pad", columns=self.num_pads, column_pitch=self.pad_spacing, port_orientation=270, size=(self.pad_size, self.pad_size), centered_ports=False, layer=(13,0))
        pad_array_ex = self.component << gf.components.pad_array("pad", columns=self.num_pads, column_pitch=self.pad_spacing, port_orientation=270, size=(self.pad_size + 2 * self.pad_tolerance, self.pad_size + 2 * self.pad_tolerance), layer=(12,0), centered_ports=False,auto_rename_ports=True)

 
        for pad_array in (pad_array_in, pad_array_ex):
            pad_array.movex(-self.num_pads / 2 * self.pad_spacing + self.pad_size / 2 + 500)
            pad_array.movey(self.pad_clearance)
        
        for port in range(self.num_pads):
            self.component.add_port(port=pad_array_ex[f"e{10-port}"],name=f"Pad_{port}")

        return pad_array_ex
    
    def add_grating_coupler(self, pos=[[0,140],[1400,140]]):

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
        
        idx = 0
        for i in range(self.grating_number):
            antgc_ref = self.component << antgc.copy()
            
            antgc_ref.dmove(   # con dmove puoi spostare nel punto desiderato al posto che move "relativo"
            origin=(antgc_ref.x, antgc_ref.y), # .x e .y ritornano il centro del componente
            destination=(pos[idx][0]+((2*idx-1)*self.fiberarray_clearance),
                            pos[idx][1]-(self.fiberarray_spacing*(i-1))))
            antgc_ref.drotate(angle=90+(idx*180), center=antgc_ref.center)

            # shadow_rect = self.component << gf.components.rectangle(size=(0.5, 0.5), layer=self.layer_wg, port_type="optical") # needed because add port is broken as of 9.7.0
            shadow_rect = self.component << gf.components.taper(length=1, width1=0.5, port=None, width2=self.wg_w, layer=self.layer_wg)
            shadow_rect.connect("o1", antgc_ref["o1"],allow_width_mismatch=True),
            self.component.add_port(f"Grating{idx}_{i}", port=shadow_rect["o2"])


    

    def interconnect_custom(self):

        my_route_s = gf.cross_section.strip(
            width=self.wg_w,                # same as route_width=5
            layer=self.layer_wg,           # same as your original routing_layer usage
            radius_min=1
        )

        my_route_e = gf.cross_section.metal_routing(
            width=15,
            layer=(12,0),
        )

        crossing_only = gf.components.waveguides.crossing_etched(width=self.wg_w)
        crossing_function = gf.components.waveguides.crossing45(crossing=crossing_only, port_spacing=20, cross_section=my_route_s, cross_section_bends=my_route_s)
        
        # crossing_function = gf.components.waveguides.crossing_etched()



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
            cross_section=my_route_s,
            allow_width_mismatch=True)
        

        c4 = self.component << crossing_function.copy()
        c4.dmove(origin=(c4.x, c4.y), destination=(930,100))

        gf.routing.route_bundle_sbend(component=self.component,
            ports2=[self.component["o_9_1"],self.component["o_6_4"],self.component["o_5_3"],self.component["o_8_2"],self.component["o_7_1"],aux1["o3"],c4["o3"],c4["o1"]],
            ports1=[self.component["o_6_3"],c4["o4"],c4["o2"],self.component["o_5_4"],self.component["o_4_3"],self.component["o_7_2"],self.component["o_9_2"],self.component["o_8_1"]],
            cross_section=my_route_s,
            allow_width_mismatch=True)
        
        gf.routing.route_bundle_sbend(component=self.component,
            ports2=[self.component["o_3_1"],self.component["o_2_1"],self.component["o_1_2"]],
            ports1=[self.component["Grating0_1"],self.component["Grating0_2"],self.component["Grating0_3"]],
            cross_section=my_route_s,
            allow_width_mismatch=True)
        
        gf.routing.route_bundle(component=self.component,
            ports2=[self.component["o_7_4"],self.component["o_8_3"],self.component["o_9_3"]],
            #ports1=[self.component["Grating1_2"],self.component["Grating1_1"],self.component["Grating1_0"]],
            ports1=[self.component["Grating0_4"],self.component["Grating0_5"],self.component["Grating0_6"]],
            cross_section=my_route_s)
        
        bend1 = self.component << gf.components.bend_circular(width=self.wg_w,radius = 15, angle = 180)
        bend1.connect("o1",self.component["Grating0_0"])
        straight1 = self.component << gf.components.straight(length=50,cross_section=my_route_s)
        straight1.connect("o1",bend1["o2"])

        bend2 = self.component << gf.components.bend_circular(width=self.wg_w,radius = 15, angle = -180)
        bend2.connect("o1",self.component["Grating0_7"])
        straight2 = self.component << gf.components.straight(length=50,cross_section=my_route_s)
        straight2.connect("o1",bend2["o2"])

        gf.routing.route_single(component=self.component, port1=straight1["o2"], port2=straight2["o2"], cross_section=my_route_s)

        ports1=[]
        ports2=[]
        portsP=[]
        for i in range(9):
            ports1.append(self.component[f"e_{i+1}_1"])
            ports2.append(self.component[f"e_{i+1}_2"])
            portsP.append(self.component[f"Pad_{i}"])
        new_ports=[]
        routes, ports = gf.routing.route_ports_to_side(component=self.component,
                                       ports=ports1[0:3],
                                       side="north",
                                       radius=0,
                                       cross_section=my_route_e,
                                       separation=20+10)
        
        routes, portsn = gf.routing.route_ports_to_side(component=self.component,
                                       ports=ports2[0:3],
                                       side="south",
                                       radius=0,
                                       cross_section=my_route_e,
                                       separation=20+15)

        new_ports.extend(ports[::-1])
        routes, ports = gf.routing.route_ports_to_side(component=self.component,
                                       ports=ports1[3:6],
                                       side="north",
                                       radius=0,
                                       cross_section=my_route_e,
                                       separation=20+15)
        routes, portsn = gf.routing.route_ports_to_side(component=self.component,
                                       ports=ports2[3:6],
                                       side="south",
                                       radius=0,
                                       cross_section=my_route_e,
                                       separation=20+15)
        
        new_ports.extend(ports[::-1])
        routes, ports = gf.routing.route_ports_to_side(component=self.component,
                                       ports=ports1[6:9],
                                       side="north",
                                       radius=0,
                                       cross_section=my_route_e,
                                       separation=20+15)
        routes, portsn = gf.routing.route_ports_to_side(component=self.component,
                                       ports=ports2[6:9],
                                       side="south",
                                       radius=0,
                                       cross_section=my_route_e,
                                       separation=20+10)
        
        
        new_ports.extend(ports[::-1])
        # print(new_ports)
        # print(ports1)
        gf.routing.route_bundle_electrical(component=self.component, 
                                           ports1=new_ports, ports2=portsP,
                                           cross_section=my_route_e,
                                           separation=20+15)

master_component=gf.Component("Neuromorphic_Chip")
MZI = MZI_sw(
    component=master_component,
    wg_w=0.48,
    arm_l=150,
    mmi_l=43.5,
    mmi_w=6.03,
    mmi_gap=0.47,
    mmi_taper_l=10,
    arm_dl=0,
    pad_clearance=1500
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

MZI.add_pads()

MZI.interconnect_custom()





# master_component.pprint_ports()
# master_component.draw_ports()
master_component.write_gds(f"mzi_test.gds")


