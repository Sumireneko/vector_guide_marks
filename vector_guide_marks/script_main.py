import krita
import os
import xml.etree.ElementTree as ET
import math, re, uuid

try:
    if int(krita.qVersion().split('.')[0]) == 5:
        raise
    from PyQt6 import uic
    from PyQt6.QtWidgets import *
    from PyQt6.QtGui import QTransform
except:
    from PyQt5 import uic
    from PyQt5.QtWidgets import *
    from PyQt5.QtGui import QTransform

from krita import *
from .size_data import sizes,fixed_sizes


# Update issue resolution
is_updating = False
reinit_requested = False
is_offsetting = False


PT_EQ_1MM = 2.83465

app = Krita.instance()

# Example configuration
"""
params = {
    'mode':'direct',
    'preset':'Free',
    'size_type': 'Sizes', # 'B4' etc

    'dpi': 72,
    'use_bleed': True,
    'bleed': 3,#default 3mm
    'lenCorner': 7,# length of the corner trim-marks
    'centerWing': 18,
    'centerPerp': 4.5,
    'centerOffset': 2,
    'stroke': 0.5,
    'crop_style': 'default', # 'jp_trim' or 'default'
    'size_mode': 'paper',# default or paper
    'size_dir': 'vertical',
    'prefix':'preview_',
    'frame': False,
    'slice': False,
    'vcol_split':1,# It should be 1
    'vrow_split':1,# It should be 1
    'vcol_spc':1,
    'vrow_spc':1,
    'vtotal_w':1,
    'vtotal_h':1,
    'vunit_w':1,
    'vunit_h':1,


    'vcol_spc_mm': 12.0,     # Display
    'vcol_spc_inch': 0.472,  # Display
    'vcol_spc_px': 45.3,      # Display

    'vrow_spc_mm': 12.0,     # Display
    'vrow_spc_inch': 0.472,  # Display
    'vrow_spc_px': 45.3,      # Display

    'vtotal_w_mm': 12.0,     # Display
    'vtotal_w_inch': 0.472,  # Display
    'vtotal_w_px': 45.3,      # Display

    'vtotal_h_mm': 12.0,     # Display
    'vtotal_h_inch': 0.472,  # Display
    'vtotal_h_px': 45.3,      # Display


    'vunit_w_mm': 12.0,     # Display
    'vunit_w_inch': 0.472,  # Display
    'vunit_w_px': 45.3,      # Display

    'vunit_h_mm': 12.0,     # Display
    'vunit_h_inch': 0.472,  # Display
    'vunit_h_px': 45.3,      # Display

    'txt_capa': False,
    'ignore_shape': False,
    'grid_size_mode': "unit",
    'use_guide': False,
    'info': True,
    'dimension': False,
    'dim_scale': True,
    'dim_scale_factor': 1,
    'dim_w': True,
    'dim_h': True,

    'dbg_wpad': 0.53,
    'dbg_dpad': 3.05,

    'unit_mode':'mm',
    'old_unit_mode':'mm',

    'rounded_corners':False,
    'roundness': 0,

    'unit_cut_guide':False,
    'preview':True

}
"""





SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


DISP_DPI=300
t= False
def conv_mm_to_inch(mm):  ast(mm / 25.4,t)             ;return mm / 25.4
def conv_mm_to_px(mm):    ast((mm / 25.4) * DISP_DPI,t);return (mm / 25.4) * DISP_DPI
def conv_mm_to_pt(mm):    ast((mm / 25.4) * 72,t)      ;return (mm / 25.4) * 72
def conv_inch_to_mm(inch):ast(inch * 25.4,t)           ;return inch * 25.4
def conv_px_to_mm(px):    ast(px / DISP_DPI * 25.4,t)  ; return px / DISP_DPI * 25.4

def ast(v,t):
    if t:print(v)

# Converts points to pixels (no need dpi)
def pt_to_px_factory(dpi):
    px_per_pt = dpi / 72
    return lambda val: val * px_per_pt, px_per_pt


# Creates the root SVG element
def create_svg_root(width, height):
    return ET.Element("{%s}svg" % SVG_NS, {
        "width": str(width)+"pt",
        "height": str(height)+"pt",
        "viewBox":f"0 0 {width} {height}",
        "version": "1.1"#,
        #"xmlns": SVG_NS
    })

# Adds a path element to the SVG
def add_path(parent, d, stroke_width,stroke_color="black"):
    ET.SubElement(parent, "{%s}path" % SVG_NS, {
        "d": d,
        "fill": "none",
        "stroke": str(stroke_color),
        "stroke-width": str(stroke_width),
        "stroke-linecap": "butt",
        "stroke-linejoin": "bevel",  # Fixes bounding box issue: using 'miter' increases size (Krita sets 'miter' by default)
        "shape-rendering": "crispEdges"
    })

# Adds by svg text
def add_svg_path(svg_element,d, stroke_width):
    path_element = (
        f'<path d="{d}" '
        f'fill="none" '
        f'stroke="black" '
        f'stroke-width="{stroke_width}" '
        f'stroke-linecap="butt" '
        f'stroke-linejoin="bevel" '
        f'shape-rendering="crispEdges" />'
    )
    svg_element.append(path_element)
    return svg_element


# Generates a simple line path
def line_path(x1, y1, x2, y2):
    return f"M {x1} {y1} L {x2} {y2}"

# Generates a corner-style path with three points
def line_path_corner(x1, y1, x2, y2, x3, y3):
    return f"M {x1} {y1} L {x2} {y2} L {x3} {y3}"

# Generates any path from list
def list_to_path(coords):
    if len(coords) < 2 or len(coords) % 2 != 0:
        raise ValueError("Error, even number required")

    path = f"M {coords[0]} {coords[1]}"
    for i in range(2, len(coords), 2):
        path += f" L {coords[i]} {coords[i+1]}"
    return path



# Adds a registration mark (circle + cross)
def add_registration_mark(parent, x, y, radius=2, cross_length=6,stroke_width=1):
    ET.SubElement(parent, "{%s}circle" % SVG_NS, {
        "cx": str(x),
        "cy": str(y),
        "r": str(radius),
        "stroke": "black",
        "stroke-width": str(stroke_width),
        "fill": "none"
    })
    ET.SubElement(parent, "{%s}line" % SVG_NS, {
        "x1": str(x - cross_length / 2),
        "y1": str(y),
        "x2": str(x + cross_length / 2),
        "y2": str(y),
        "stroke-width": str(stroke_width),
        "stroke": "black"
    })
    ET.SubElement(parent, "{%s}line" % SVG_NS, {
        "x1": str(x),
        "y1": str(y - cross_length / 2),
        "x2": str(x),
        "y2": str(y + cross_length / 2),
        "stroke-width": str(stroke_width),
        "stroke": "black"
    })

def add_rect(parent, x, y, rect_width=5, rect_height=5,stroke_width=1,stroke="black",radius=0):
    ET.SubElement(parent, "{%s}rect" % SVG_NS, {
        "x": str(x),#+stroke_width/2
        "y": str(y),#+stroke_width/2
        "width": str(rect_width),
        "height": str(rect_height),
        "fill": "none",
        "stroke-linejoin": "bevel",
        "stroke": stroke ,
        "id":"tid_",
        "rx":str(radius),
        "ry":str(radius),
        "stroke-width": str(stroke_width),
    })

def add_rect_fill(parent, x, y, rect_width=5, rect_height=5,stroke_width=1,stroke="black",radius=0):
    ET.SubElement(parent, "{%s}rect" % SVG_NS, {
        "x": str(x),#+stroke_width/2
        "y": str(y),#+stroke_width/2
        "width": str(rect_width),
        "height": str(rect_height),
        "fill":  stroke,
        "stroke-linejoin": "bevel",
        "stroke": stroke ,
        "id":"tid_",
        "rx":str(radius),
        "ry":str(radius),
        "stroke-width": str(stroke_width),
    })


def add_text(parent, x, y, text_content, font_family="Arial", font_size=9, fill="black"):
    ET.SubElement(parent, "{%s}text" % SVG_NS, {
        "x": str(x),
        "y": str(y),
        "font-size": str(font_size),
        "fill": fill,
        "stroke-width": "0.15",
        "stroke": "white",
        "font-family": font_family,
        "xml:space": "preserve"
    }).text = text_content


# scale_factor 1 for shape-size
def S(val,scale_factor=1):
    return val * scale_factor

# conv unit for display
def conv_unit(unit_mode,size_w,size_h):
    if unit_mode == "mm":
        pass # Default
    elif unit_mode == "inch":
        size_h=conv_mm_to_inch(size_h)
        size_w=conv_mm_to_inch(size_w)
    elif unit_mode == "px":
        size_h=conv_mm_to_px(size_h)
        size_w=conv_mm_to_px(size_w)

    return (size_w,size_h)

# Main drawing function
def draw_cropmarks(shape_count,doc,trans,params,x,y,width,height,prefix):
    mm, px_per_mm = pt_to_px_factory(params['dpi'])

    # Convert all params values to pixels

    # PT_EQ_1MM = 2.83465pt ≈ 1mm

    if params['dimension']==True:
        bleed = 0
    else:
        bleed = float(params['bleed'])*PT_EQ_1MM # 3


    buni = 3.0*PT_EQ_1MM 
    CL = 3.0*PT_EQ_1MM 
    L = buni*2.5# 7
    wing_half = buni*6 / 2#18
    perp = buni*3 / 2 # 4.5 center mark
    offset = buni * 4 / 6 # 2 centerOffset 

    # Stroke and line settings
    stroke_px = 0.5# stroke width
    dim_stroke_px = stroke_px
    frame_stroke_px = 2
    trimmark_stroke_px = 0.5
    grid_stroke_px  = 1
    crop_length = CL  # The unit of cropmark line length (3mm)

    # Simulated target bounding box (replace with actual if needed)
    wpt = doc.width()*0.72
    hpt = doc.height()*0.72
    svg = create_svg_root(str(wpt), str(hpt))
    newtag = f' width="{wpt}pt" height="{hpt}pt" viewBox="0 0 {wpt} {hpt}" '
    tonbo_group = ET.SubElement(svg, "{%s}g" % SVG_NS, {
        "id": prefix+"_"+str(uuid.uuid4())[:8],
        "fill": "none",
        "stroke": "rgb(0,0,0)",
        # "stroke-width": str(stroke_px),
        "stroke-linecap": "butt",
        "stroke-linejoin": "bevel",
        "shape-rendering": "crispEdges",
        "transform":trans
    })


    # Grid Slice
    s_slice = params['slice']
    if s_slice is True and params.get("ignore_shape") == True:
        width = params['vtotal_w'] * PT_EQ_1MM
        height = params['vtotal_h'] * PT_EQ_1MM

    left, right = x - bleed, x + width + bleed
    top, bottom = y - bleed, y + height + bleed
    cx, cy = (left + right) / 2, (top + bottom) / 2

    # scale
    scale = params['dim_scale_factor'] if params['dim_scale_factor']>1 and params['dimension']==True else 1
    size_w = width*(25.4/72)*scale # mm
    size_h = height*(25.4/72)*scale

    # mm , px ,inch (Default:mm)
    unit_mode = params['unit_mode']
    disp_size_w,disp_size_h = conv_unit(unit_mode,size_w,size_h)
    disp_bleed ,_           = conv_unit(unit_mode,float(params['bleed']),0)

    # size 
    fsize = PT_EQ_1MM*9*0.25

    rfactor = 2
    if params['dim_scale_factor']>5:rfactor = 1
    if params['dim_scale_factor']>8:rfactor = 0

    disp_size_w = str(round(disp_size_w,rfactor))
    disp_size_h = str(round(disp_size_h,rfactor))
    disp_bleed  = str(round(disp_bleed ,3))
    disp_dpi = f"({DISP_DPI}dpi)" if params['unit_mode']=='px' else ""

    if params['dimension'] is False and params['info'] is True:

        type_name = "Paper size: "+params['size_type']+" ("+params['size_dir']+")" if params['preset'] != "Free" else ""

        prop = f"W x H: {disp_size_w} x {disp_size_h}{unit_mode} {disp_dpi}" # ({doc.width()} x {doc.height()}px)"
        prop2 = f"{type_name}";s_ofs=-1# display position
        
        if params['use_bleed'] is True:
            s_ofs=2
            prop2 = prop2+f" Bleed: {disp_bleed}{unit_mode}"# ({bleed}px)
    
        swx  = S(x+(width*0.5)-(len(prop)*fsize)*0.25)
        swx2 = S(x+(width*0.5)-(len(prop2)*fsize)*0.25)
        swy = S(top-bleed*0.15-offset-fsize*s_ofs)
        swy2 = S(top-bleed*0.15-offset-fsize)
    
        shx = S(right)
        shy = S(y+height*0.5+fsize*0.5)

        add_text(tonbo_group, swx , swy , prop  ,"Arial",fsize)# size
        add_text(tonbo_group, swx2, swy2, prop2 ,"Arial",fsize)# bleed




    elif params['dimension'] is True:
        pad = 2*PT_EQ_1MM # 3mm

        scaling = f"Scale:1/{params['dim_scale_factor']} Unit:{unit_mode}{disp_dpi}"
        prop = f"{scaling}"
        prop2 = f"{disp_size_w}"
        swx  = S(x+(width*0.5)-(len(prop)*fsize)*0.25)
        swx2 = S(x+(width*0.5)-(len(prop2)*fsize)*0.25)
        swy = S(top-pad*0.3-offset-fsize*1.6)
        swy2 = S(top-pad*0.3-offset-fsize*0.5)
    
        shx = S(right+pad*1.35)
        shy = S(y+height*0.5+fsize*0.5)

        # mm , px ,inch 
        unit_mode = params['unit_mode']
        size_w,size_h = conv_unit(unit_mode,size_w,size_h)


        if params['dim_scale'] is True and shape_count==0:
            # Scale info display only 1st shape (on top-front shape)
            add_text(tonbo_group, swx , swy , prop  ,"Arial",fsize)#scale
        if params['dim_w'] is True:
            add_text(tonbo_group, swx2, swy2, prop2 ,"Arial",fsize)
            add_path(tonbo_group, list_to_path([ left , (top - pad*0.25) , left, (top - pad*1.2), right, top - pad*1.2, right , (top - pad*0.25)]) , S(dim_stroke_px))
            #add_svg_path(aux_tonbo_group, list_to_path([ left , (top - pad*0.25) , left, (top - pad*1.2), right, top - pad*1.2, right , (top - pad*0.25)]) , S(dim_stroke_px))

        if params['dim_h'] is True:
            add_text(tonbo_group, shx, shy,disp_size_h,"Arial",fsize)
            add_path(tonbo_group, list_to_path([ (right + pad*0.25) , top , (right + pad*1.2), top , (right + pad*1.2), bottom , (right + pad*0.25) , bottom]) , S(dim_stroke_px))
            #add_svg_path(aux_tonbo_group, list_to_path([ (right + pad*0.25) , top , (right + pad*1.2), top , (right + pad*1.2), bottom , (right + pad*0.25) , bottom]) , S(dim_stroke_px))


    # rect(Frame)
    if params['frame'] is True:
        stroke_w = stroke_px*2.5 if not params['dimension'] else 0
        radius =  params['roundness'] if params['rounded_corners'] is True else 0
        add_rect(tonbo_group,S(x,1), S(y,1),S(width,1),  S(height,1), S(frame_stroke_px,1),"black",radius)


    # Grid Slice
    if s_slice is True:

        #print("debug orig_raw:",width,height)
        #print("Grid size mode:", params["grid_size_mode"])

        update_grid_layout(params,width/PT_EQ_1MM,height/PT_EQ_1MM)


        draw_rect_grid(params, tonbo_group, x, y,  params["vtotal_w"], params["vtotal_h"],
                    params["vcol_split"], params["vrow_split"],
                    params["vcol_spc"] * PT_EQ_1MM,
                    params["vrow_spc"] * PT_EQ_1MM,
                    stroke=grid_stroke_px, color="black")

    crop_style = params.get("crop_style", "default")


    prop3=""
    if params['txt_capa']==True:
        vc_spl = params['vcol_split'];vr_spl=params['vrow_split']
        if params['vcol_spc']==0 and params['vrow_spc']>0:#params['size_dir']=="vertical"
            prop3 = f"{vc_spl}W x {vr_spl}L = {vr_spl*vc_spl}"
        elif params['vrow_spc']==0 and params['vcol_spc']>0:#params['size_dir']=="horizontal"
            prop3 = f"{vr_spl}W x {vc_spl}L = {vr_spl*vc_spl}"

        swx3 = S(x)
        swy3 = S(bottom+L*0.15)
        add_text(tonbo_group, swx3, swy3, prop3 ,"Arial",fsize*1.5,fill="#0097E1")# text capacity



    if params['dimension'] is False and params['use_bleed'] is True:

        if crop_style == "jp_trim":
            # Japanese-style corner trim marks (8 paths)
            add_path(tonbo_group, line_path_corner(S(left - L), S(top + crop_length), S(left), S(top + crop_length), S(left), S(top - L)), S(trimmark_stroke_px))
            add_path(tonbo_group, line_path_corner(S(left - L), S(top), S(left + crop_length), S(top), S(left + crop_length), S(top - L)), S(trimmark_stroke_px))
            add_path(tonbo_group, line_path_corner(S(right + L), S(top + crop_length), S(right), S(top + crop_length), S(right), S(top - L)), S(trimmark_stroke_px))
            add_path(tonbo_group, line_path_corner(S(right + L), S(top), S(right - crop_length), S(top), S(right - crop_length), S(top - L)), S(trimmark_stroke_px))
            add_path(tonbo_group, line_path_corner(S(left - L), S(bottom), S(left + crop_length), S(bottom), S(left + crop_length), S(bottom + L)), S(trimmark_stroke_px))
            add_path(tonbo_group, line_path_corner(S(left - L), S(bottom - crop_length), S(left), S(bottom - crop_length), S(left), S(bottom + L)), S(trimmark_stroke_px))
            add_path(tonbo_group, line_path_corner(S(right + L), S(bottom), S(right - crop_length), S(bottom), S(right - crop_length), S(bottom + L)), S(trimmark_stroke_px))
            add_path(tonbo_group, line_path_corner(S(right + L), S(bottom - crop_length), S(right), S(bottom - crop_length), S(right), S(bottom + L)), S(trimmark_stroke_px))
    
            # Japanese-style center trim marks (8 paths)
            add_path(tonbo_group, line_path(S(cx - wing_half), S(top - offset), S(cx + wing_half), S(top - offset)), S(trimmark_stroke_px))
            add_path(tonbo_group, line_path(S(cx), S(top), S(cx), S(top - perp)), S(trimmark_stroke_px))
            add_path(tonbo_group, line_path(S(cx - wing_half), S(bottom + offset), S(cx + wing_half), S(bottom + offset)), S(trimmark_stroke_px))
            add_path(tonbo_group, line_path(S(cx), S(bottom), S(cx), S(bottom + perp)), S(trimmark_stroke_px))
            add_path(tonbo_group, line_path(S(left - offset), S(cy - wing_half), S(left - offset), S(cy + wing_half)), S(trimmark_stroke_px))
            add_path(tonbo_group, line_path(S(left), S(cy), S(left - perp), S(cy)), S(trimmark_stroke_px))
            add_path(tonbo_group, line_path(S(right + offset), S(cy - wing_half), S(right + offset), S(cy + wing_half)), S(trimmark_stroke_px))
            add_path(tonbo_group, line_path(S(right), S(cy), S(right + perp), S(cy)), S(trimmark_stroke_px))
    
        else:
            # European-style corner trim marks (8 paths)
            add_path(tonbo_group, line_path(S(left - L), S(top + crop_length), S(left), S(top + crop_length)), S(trimmark_stroke_px))
            add_path(tonbo_group, line_path(S(left + crop_length), S(top), S(left + crop_length), S(top - L)), S(trimmark_stroke_px))
            add_path(tonbo_group, line_path(S(right + L), S(top + crop_length), S(right), S(top + crop_length)), S(trimmark_stroke_px))
            add_path(tonbo_group, line_path(S(right - crop_length), S(top), S(right - crop_length), S(top - L)), S(trimmark_stroke_px))
            add_path(tonbo_group, line_path(S(left - L), S(bottom - crop_length), S(left), S(bottom - crop_length)), S(trimmark_stroke_px))
            add_path(tonbo_group, line_path(S(left + crop_length), S(bottom), S(left + crop_length), S(bottom + L)), S(trimmark_stroke_px))
            add_path(tonbo_group, line_path(S(right + L), S(bottom - crop_length), S(right), S(bottom - crop_length)), S(trimmark_stroke_px))
            add_path(tonbo_group, line_path(S(right - crop_length), S(bottom), S(right - crop_length), S(bottom + L)), S(trimmark_stroke_px))
    
            # Registration marks (4 circles + crosses)
            voffset = L * 0.45
            vradius = L * 0.25
            cross_length = L
            add_registration_mark(tonbo_group, S(left - voffset), S(top - voffset), S(vradius), S(cross_length),S(trimmark_stroke_px))
            add_registration_mark(tonbo_group, S(right + voffset), S(top - voffset), S(vradius), S(cross_length),S(trimmark_stroke_px))
            add_registration_mark(tonbo_group, S(left - voffset), S(bottom + voffset), S(vradius), S(cross_length),S(trimmark_stroke_px))
            add_registration_mark(tonbo_group, S(right + voffset), S(bottom + voffset), S(vradius), S(cross_length),S(trimmark_stroke_px))
    
    if  params['use_guide'] is True:#params['dimension'] is False and
        Lo = L+6# line extend offset
        lt=f"M {left-Lo} {top+bleed} L {right+Lo} {top+bleed}"# Draw a horizontal line from left to right (top edge)
        lb=f"M {left-Lo} {bottom-bleed} L {right+Lo} {bottom-bleed}"# Draw a horizontal line from left to right (bottom edge)
        ll=f"M {left+bleed} {top-Lo} L {left+bleed} {bottom+Lo}"# Draw a vertical line top to bottom (left edge)
        lr=f"M {right-bleed} {top-Lo} L {right-bleed} {bottom+Lo}"# Draw a vertical line top to bottom (right edge)

        add_path(tonbo_group, lt , S(trimmark_stroke_px*0.5), "green")
        add_path(tonbo_group, lb , S(trimmark_stroke_px*0.5), "green")
        add_path(tonbo_group, ll , S(trimmark_stroke_px*0.5), "green")
        add_path(tonbo_group, lr , S(trimmark_stroke_px*0.5), "green")




    # Save SVG to file
    svg_str = ET.tostring(svg, encoding="utf-8", method="xml").decode("utf-8")

    # print(svg_str)
    return svg_str



def limit_unit_by_total(total_value):
    # Prevent unit size >>> Total size
    max_unit = int(total_value / 1.0)  # minimum: 1.0mm
    return min(max_unit, 128)



def qtransform_to_svg_transform(transform: QTransform):
    """Convert QTransform to SVG transform attribute format
    transform = QTransform(1, 0, 0, 1, 100, 200)
    svg_transform = qtransform_to_svg_transform(transform)
    print(svg_transform)  # "matrix(1 0 0 1 100 200)"
    """
    return f"matrix({transform.m11()} {transform.m12()} {transform.m21()} {transform.m22()} {transform.m31()} {transform.m32()})"

def pt_to_px(pt, dpi=300):return pt * dpi / 96
def mm_to_pt(mm): return mm * PT_EQ_1MM
def pt_to_mm(pt): return pt / PT_EQ_1MM

def draw_rect_grid(params, group, start_x, start_y, total_width, total_height,
                   cols, rows, h_padding=0, v_padding=0,
                   stroke=1, color="black"):

    """
    Parameters:
    - group: append svg target
    - start_x, start_y: position 
    - total_width, total_height: original size
    - cols, rows: The count number of slices
    - h_padding, v_padding: paddings 
    - color: rect color
    - stroke: stroke width
    """
    if cols <= 1:
       params['vcol_spc'] = h_padding = 0
    if rows <= 1:
       params['vrow_spc'] = v_padding = 0


    rect_width = params['vunit_w'] * PT_EQ_1MM
    rect_height = params['vunit_h'] * PT_EQ_1MM
    h_padding = params['vcol_spc'] * PT_EQ_1MM
    v_padding = params['vrow_spc'] * PT_EQ_1MM

    # text capacity 
    cflg = params['txt_capa']
    cflg_col = True if cflg and params['vcol_spc']==0 and params['vrow_spc']>0 else False
    cflg_row = True if cflg and params['vrow_spc']==0 and params['vcol_spc']>0 else False
    if cflg:color = "#0097E1"
    radius =  params['roundness'] if params['rounded_corners'] is True else 0

    gd ="";Lk=3*PT_EQ_1MM
    last_x = start_x+total_width*PT_EQ_1MM
    last_y = start_y+total_height*PT_EQ_1MM

    # Draw the grid
    for row in range(rows):
        for col in range(cols):
            px = start_x + col * (rect_width + h_padding)
            py = start_y + row * (rect_height + v_padding)
            fillcolor=""
            # Text capacity
            capa = handle_capa_fill(cflg, cflg_col, cflg_row, row, col, group, px, py, rect_width, rect_height, stroke, color, radius)
            if capa==True:continue
            # Grid unit
            add_rect(group, px, py, rect_width, rect_height, stroke, color,radius)
            # Unit cut guide
            if params['unit_cut_guide']:
                gd=add_unit_cut_guide(gd, row, col, px, py, start_x, start_y, last_x, last_y, h_padding, v_padding, Lk)

    if len(gd)>0:
        gd=gd+add_final_unit_cut_guides(gd, rows, cols, start_x, start_y, rect_width, rect_height, h_padding, v_padding, last_x, last_y, Lk)
        add_path(group, gd , 0.35,"green")


def handle_capa_fill(capa_flg, capa_flg_col, capa_flg_row, row, col, group, px, py, rect_width, rect_height, stroke, color, radius):
    if not capa_flg:
        return False 

    if capa_flg_col and col > 1 and (col + 1) % 10 == 0:
        add_rect_fill(group, px, py, rect_width, rect_height, stroke, color, radius)
        return True 

    if capa_flg_row and row > 1 and (row + 1) % 10 == 0:
        add_rect_fill(group, px, py, rect_width, rect_height, stroke, color, radius)
        return True   

    return False




def add_unit_cut_guide(gd, row, col, px, py, start_x, start_y, last_x, last_y, h_padding, v_padding, Lk):
    # col 
    if row == 0 and col > -1:
        gd += f"M{px - h_padding * 0.5} {start_y - Lk} L{px - h_padding * 0.5} {start_y - Lk * 2}"
        gd += f"M{px - h_padding * 0.5} {last_y + Lk} L{px - h_padding * 0.5} {last_y + Lk * 2}"
    # row 
    if col == 0 and row > -1:
        gd += f"M{start_x - Lk} {py - v_padding * 0.5} L{start_x - Lk * 2} {py - v_padding * 0.5}"
        gd += f"M{last_x + Lk} {py - v_padding * 0.5} L{last_x + Lk * 2} {py - v_padding * 0.5}"
    return gd

def add_final_unit_cut_guides(gd, rows, cols, start_x, start_y, rect_width, rect_height, h_padding, v_padding, last_x, last_y, Lk):
    # last vertical
    px_last = start_x + (cols ) * (rect_width + h_padding)
    gd += f"M{px_last -  h_padding * 0.5} {start_y - Lk} L{px_last - h_padding * 0.5} {start_y - Lk * 2}"
    gd += f"M{px_last -  h_padding * 0.5} {last_y  + Lk} L{px_last - h_padding * 0.5} {last_y  + Lk * 2}"

    # last horizontal
    py_last = start_y + (rows ) * (rect_height + v_padding)
    gd += f"M{start_x - Lk} {py_last - v_padding * 0.5} L{start_x - Lk * 2} {py_last - v_padding * 0.5}"
    gd += f"M{last_x  + Lk} {py_last - v_padding * 0.5} L{last_x  + Lk * 2} {py_last - v_padding * 0.5}"

    return gd



def is_rect_size_active(params, selected_rect_width, selected_rect_height):
    vtotal_w = params.get('vtotal_w')
    vtotal_h = params.get('vtotal_h')
    if not vtotal_w or not vtotal_h:
        return False
    return vtotal_w == selected_rect_width and vtotal_h == selected_rect_height


def update_grid_params(params, total_width, total_height, cols, rows, h_padding, v_padding):
    if cols <= 1:
       params['vcol_spc'] = h_padding = 0
    if rows <= 1:
       params['vrow_spc'] = v_padding = 0

    rect_width = max(1, (total_width - h_padding * max(0, cols - 1)) / cols)
    rect_height = max(1, (total_height - v_padding * max(0, rows - 1)) / rows)
    params['vunit_w'] = rect_width
    params['vunit_h'] = rect_height






# ----------------
# Combination
# ----------------

def from_mm_(value, unit_mode):
    if unit_mode == "inch":
        return conv_mm_to_inch(value)
    elif unit_mode == "px":
        return conv_mm_to_px(value)
    elif unit_mode == "mm":# mm(default)
        return value
    return value 

def to_mm_(value, unit_mode):
    if unit_mode == "inch":
        return conv_inch_to_mm(value)
    elif unit_mode == "px":
        return conv_px_to_mm(value)
    elif unit_mode == "mm":# mm(default)
        return value
    return value  



def set_to_all_unit_(params,key,value):

    #print("set_to_all_unit:")
    # params[key]=value
    params[key+"_mm"]=value
    params[key+"_px"]=conv_mm_to_px(value)
    params[key+"_inch"]=conv_mm_to_inch(value)


    return value


def update_grid_layout(params, original_width, original_height):
    mode = params.get("grid_size_mode", "total")
    cols = max(params.get("vcol_split", 1), 1)
    rows = max(params.get("vrow_split", 1), 1)
    ignore_shape = params.get("ignore_shape", False)
    unit_mode = "mm"



    # Step 0: Special case for single split
    if cols == 1:
        params["vcol_spc"] = 0
        params["vunit_w"] = params["vtotal_w"]
    if rows == 1:
        params["vrow_spc"] = 0
        params["vunit_h"] = params["vtotal_h"]


    # Step 1: Fix total size if ignore_shape is False
    if not ignore_shape:
        # Only overwrite if original size is valid and larger than zero
        if original_width > 0:
            params['vtotal_w'] = original_width
        if original_height > 0:
            params['vtotal_h'] = original_height

    # Step 2: Mode-based recalculation
    if mode == "unit":
        recalculate_space_from_unit(params, unit_mode, cols, rows)
        if not ignore_shape:
            adjust_spacing_to_fit_total(params, cols, rows)
    elif mode == "space":
        recalculate_unit_from_space(params, unit_mode, cols, rows)
    elif mode == "total" and ignore_shape:
        recalculate_unit_from_total(params, unit_mode, cols, rows)

    # Step 2.5: Limit unit size when space is zero and total is fixed (ignore_shape=False and mode=unit)
    limit_unit_size_when_space_zero(params, cols, rows)

    # Step 2.7: Limit space if ignore_shape is True　 ignore_shape and
    if mode == "space":
        limit_space_to_fit_original(params, original_width, original_height, unit_mode, cols, rows)

    # Step 3: Recalculate total if ignore_shape is True
    if ignore_shape:
        recalculate_total_from_unit_and_space(params, original_width, original_height, cols, rows)

    # Step 4: Fail-safe correction if ignore_shape is False
    if not ignore_shape:
        apply_fail_safe(params, cols, rows, mode)

    # Step 6: Sync all sub-unit values (px, inch, etc.)
    sync_all_units(params)






def sync_all_units(params):
    for key in ['vcol_spc', 'vrow_spc', 'vunit_w', 'vunit_h', 'vtotal_w', 'vtotal_h']:
        set_to_all_unit_(params, key, params[key])

# Step2
# change unit
def recalculate_space_from_unit(params, unit_mode, cols, rows):

    unit_w = to_mm_(params['vunit_w'], unit_mode)
    unit_h = to_mm_(params['vunit_h'], unit_mode)
    total_w = to_mm_(params['vtotal_w'], unit_mode)
    total_h = to_mm_(params['vtotal_h'], unit_mode)

    # no spacing re-calclation when ignore_shape=False (use adjust_spacing_to_fit_total)
    if params.get("ignore_shape", False):
        vc_spc = calculate_spacing(total_w, unit_w, cols)
        vr_spc = calculate_spacing(total_h, unit_h, rows)
        params['vcol_spc'] = vc_spc
        params['vrow_spc'] = vr_spc

# change spc
def recalculate_unit_from_space(params, unit_mode,   cols, rows):
    col_spc = to_mm_(params['vcol_spc'], unit_mode)
    row_spc = to_mm_(params['vrow_spc'], unit_mode)
    total_w = to_mm_(params['vtotal_w'], unit_mode)
    total_h = to_mm_(params['vtotal_h'], unit_mode)

    vu_w = calculate_unit_size(total_w, col_spc, cols) if not (params.get('vunit_w', 0) == 0 and col_spc != 0) else 0
    vu_h = calculate_unit_size(total_h, row_spc, rows) if not (params.get('vunit_h', 0) == 0 and row_spc != 0) else 0

    params['vunit_w'] = vu_w
    params['vunit_h'] = vu_h


def recalculate_unit_from_total(params, unit_mode,   cols, rows):
    total_w = to_mm_(params['vtotal_w'], unit_mode)
    total_h = to_mm_(params['vtotal_h'], unit_mode)
    col_spc = to_mm_(params['vcol_spc'], unit_mode)
    row_spc = to_mm_(params['vrow_spc'], unit_mode)

    # Recalculate unit to fit total (space remains fixed)
    vu_w = max((total_w - col_spc * max(cols - 1, 0)) / cols, 0)
    vu_h = max((total_h - row_spc * max(rows - 1, 0)) / rows, 0)
    params['vunit_w'] = vu_w
    params['vunit_h'] = vu_h


# step3
def recalculate_total_from_unit_and_space(params, original_width, original_height, cols, rows):
    max_w = (params['vunit_w'] * cols) + (params['vcol_spc'] * max(cols - 1, 0))
    max_h = (params['vunit_h'] * rows) + (params['vrow_spc'] * max(rows - 1, 0))

    # Prevent overshoot
    vt_w = min(max_w, original_width)
    vt_h = min(max_h, original_height)

    params['vtotal_w'] = vt_w
    params['vtotal_h'] = vt_h

def limit_unit_size_when_space_zero(params, cols, rows):
    # col space = 0 unit_w = max
    if params.get('vcol_spc', 0) == 0:
        max_unit_w = params['vtotal_w'] / max(cols, 1)
        if params['vunit_w'] > max_unit_w:
            params['vunit_w'] = max_unit_w

    # col space = 0 unit_h = max
    if params.get('vrow_spc', 0) == 0:
        max_unit_h = params['vtotal_h'] / max(rows, 1)
        if params['vunit_h'] > max_unit_h:
            params['vunit_h'] = max_unit_h


def limit_space_to_fit_original(params, original_width, original_height, unit_mode, cols, rows):
    original_width_mm = to_mm_(original_width, unit_mode)
    original_height_mm = to_mm_(original_height, unit_mode)
    
    max_sp_w = max((original_width_mm - params['vunit_w'] * cols) / max(cols - 1, 1), 0)
    max_sp_h = max((original_height_mm - params['vunit_h'] * rows) / max(rows - 1, 1), 0)


    if params['vcol_spc'] > max_sp_w:
        params['vcol_spc'] = max_sp_w

    if params['vrow_spc'] > max_sp_h:
        params['vrow_spc'] = max_sp_h





# if it over total size(mode=unit,space,total)(unit_mode=px,inch,mm)
def apply_fail_safe(params,   cols, rows,mode):
    # Fail-safe correction to prevent total size overflow.
    # Behavior differs depending on mode:
    # - In "unit" mode, only spacing is adjusted to fit within total size.
    # - In other modes ("space", "total"), both spacing and unit size may be adjusted.

    max_total_w = (params['vunit_w'] * cols) + (params['vcol_spc'] * max(cols - 1, 0))
    max_total_h = (params['vunit_h'] * rows) + (params['vrow_spc'] * max(rows - 1, 0))

    if max_total_w > params['vtotal_w']:
        excess_w = max_total_w - params['vtotal_w']
        new_spc = max(params['vcol_spc'] - excess_w / max(cols - 1, 1), 0)
        params['vcol_spc'] = new_spc

        max_total_w = (params['vunit_w'] * cols) + (new_spc * max(cols - 1, 0))
        if max_total_w > params['vtotal_w'] and mode != "unit":
            vu_w = max((params['vtotal_w'] - new_spc * max(cols - 1, 0)) / cols, 0)
            params['vunit_w'] = vu_w


    if max_total_h > params['vtotal_h']:
        excess_h = max_total_h - params['vtotal_h']
        new_spc = max(params['vrow_spc'] - excess_h / max(rows - 1, 1), 0)
        params['vrow_spc'] = new_spc

        max_total_h = (params['vunit_h'] * rows) + (new_spc * max(rows - 1, 0))
        if max_total_h > params['vtotal_h'] and mode != "unit":
            vu_h = max((params['vtotal_h'] - new_spc * max(rows - 1, 0)) / rows, 0)
            params['vunit_h'] = vu_h





def adjust_spacing_to_fit_total(params, cols, rows):
    # total_w/h are fixed
    total_w = params['vtotal_w']
    total_h = params['vtotal_h']
    unit_w = params['vunit_w']
    unit_h = params['vunit_h']

    params['vcol_spc'] = max((total_w - unit_w * cols) / max(cols - 1, 1), 0)
    params['vrow_spc'] = max((total_h - unit_h * rows) / max(rows - 1, 1), 0)


def calculate_spacing(total, unit, count):
    if count <= 1:
        return 0
    return max((total - unit * count) / (count - 1), 0)

def calculate_unit_size(total, spacing, count):
    return max((total - spacing * max(count - 1, 0)) / count, 0)



# ------------
#  preview
# ------------
def rm_shape(shape,prefix):
    try:
        if shape is None:
            print("Error: shape is None")
            return

        if not hasattr(shape, "name") or not callable(shape.name):
            print("Error: shape object missing 'name' method")
            return

        sname = shape.name()

        if not isinstance(sname, str):
            print("Error: shape.name() did not return string")
            return




        if sname.startswith(prefix):
            if shape and hasattr(shape, 'remove') and callable(shape.remove):
                if not getattr(shape, "_removed", False):  # delete once time with use a flag 
                    shape.remove()
                    shape._removed = True
            else:
                print(f"Cannot remove shape: {sname} — method missing or not callable")



    except Exception as e:
        print(f"Error removing shape : {e}")#{shape.name()}

def re_init(prefix):
    global is_updating, reinit_requested
    print("begin_re_init")
    if is_updating:
        print("Now re_init() running.")
        if not reinit_requested:
            print("Setting reinit_requested=True")
            reinit_requested = True
        else:
            print("Reinit already requested")
        return
    try:
        app = Krita.instance()
        doc = app.activeDocument()
        view = app.activeWindow().activeView()
        selected_layers = view.selectedNodes()
        
        if doc is None:
            print("No active document found.")
            return

        for node in selected_layers:
            if not node:continue
            print("Current Layer name",node.name())
            if node.type() == "vectorlayer":
                
                shapes = node.shapes()
                for shape in shapes:
                    rm_shape(shape,prefix)

    except Exception as e:
        print(f"[re_init] Exception occurred: {e}")
    finally:
        is_updating = False
        print("[re_init] is_updating=False")



def re_show(prefix,flg):

    app = Krita.instance()
    doc = app.activeDocument()
    view = app.activeWindow().activeView()
    selected_layers = view.selectedNodes()
    
    if doc is None:
        print("No active document found.")
        return

    for node in selected_layers:
        if node.type() == "vectorlayer":
            shapes = node.shapes()
            for shape in shapes:
                #if shape.isSelected():
                sname = shape.name()
                if sname.startswith(prefix): shape.setVisible(flg) # show or hide


def re_z_index(prefix,level=9999):

    app = Krita.instance()
    doc = app.activeDocument()
    view = app.activeWindow().activeView()
    selected_layers = view.selectedNodes()
    
    if doc is None:
        print("No active document found.")
        return

    for node in selected_layers:
        if node.type() == "vectorlayer":
            shapes = node.shapes()
            for shape in shapes:
                # if shape.isSelected():
                sname = shape.name()
                if sname.startswith(prefix): shape.setZIndex(level) # show or hide


def determine(prefix):
    new_prefix = "cropmark"
    app = Krita.instance()
    doc = app.activeDocument()

    if doc is None:
        print("No active document found.")
        return

    view = app.activeWindow().activeView()
    selected_layers = view.selectedNodes()
    prefix_len = len(prefix)

    version = app.version()
    des = True
    for node in selected_layers:
        if node.type() == "vectorlayer":
            shapes = node.shapes()
            for shape in shapes:
                if des == True and shape.isSelected():
                    shape.deselect()
                sname = shape.name()
                # if sname.startswith(prefix):shape.setName("shape"+str(uuid.uuid4())[:8]) # rename 
                if sname.startswith(prefix):
                    new_name = new_prefix + sname[prefix_len:]
                    shape.setName(new_name)

def deselectAll():
    app = Krita.instance()
    doc = app.activeDocument()

    if doc is None:
        print("No active document found.(deselection)")
        return

    view = app.activeWindow().activeView()
    selected_layers = view.selectedNodes()

    version = app.version()
    des = True
    if des == False:return
    for node in selected_layers:
        if node.type() == "vectorlayer":
            [shape.deselect() for shape in node.shapes() if shape.isSelected()]


# ------------
# paper size
# ------------
def paper_size(type="A", number=0, orientation="vertical", unit="mm",flg=""):
    base_sizes = {
        "A": (841, 1189),  # A0(iso)
        "B": (1000, 1414),  # B0(iso)
        "B(JIS)": (1030, 1456),  # B0(jis)
        "D(GB)": (889, 1194)     # D1(GB China standard)
    }

    if type == "B" and flg =="(JIS)":type=type+flg
    if type == "D" and flg =="(GB)":type=type+flg
    #print("nnnn",type,flg)

    if type.upper() == "C":
        # Calculate C0 size as the geometric mean of A0 and B0 dimensions
        a_w, a_h = base_sizes["A"]
        b_w, b_h = base_sizes["B"]
        w = math.sqrt(a_w * b_w)
        h = math.sqrt(a_h * b_h)
        for _ in range(number):
            w, h = h / 2, w  # fold in half
    else:
        w, h = base_sizes[type.upper()]
        for _ in range(number):
            w, h = h / 2, w  # fold in half


    if orientation == "horizontal":
        w, h = h, w

    if unit == "px":#px->pt
        w = round(w * PT_EQ_1MM,2)
        h = round(h * PT_EQ_1MM,2)


    return {"width": w, "height": h}

# ------------
# Paper(refill)
# ------------
def refill_size(type="Bible", orientation="vertical", unit="mm"):
    global sizes

    if type not in sizes:
        raise ValueError(f"Unknown refill type:{type}")

    w, h = sizes[type]

    if orientation == "horizontal":
        w, h = h, w

    if unit == "px":#px->pt
        w = round(w * PT_EQ_1MM,2)
        h = round(h * PT_EQ_1MM,2)

    return {"width": w, "height": h}

# ------------
# list
# ------------
def get_size(sel="A5",dir="vertical"):

    match = re.search(r'[ABCD][0-9]', sel)# Detect A1 - A7 etc.
    match_loc = re.search(r'\((JIS|GB)\)', sel)
    sel = re.sub(r'\((JIS|GB)\)', '', sel)
 
    size = []
    if match:
        # print(match.group())
        s = match.group()
        type = s[0] # paper type e.g."A" part of "A5"
        number = int(s[1:]) # "5" part of "A5"
        
        loc_flag = match_loc.group() if match_loc else None
        # print("Select:",type, number, dir, "px", loc_flag)
        size = paper_size(type, number, dir, "px", loc_flag)

    else:
        size = refill_size(sel, dir, unit="px")
    
    #print("Selected:",sel,size)
    return size

# ------------
# main
# ------------

def compute_correction_factor(actual_px, target_mm, dpi=96):
    target_px = target_mm * dpi / 25.4
    return actual_px / target_px


def main(params):
    doc = app.activeDocument()
    if not doc:
        print("Error: Document not found")
        exit()

    # state to dict (The case for GUI used)
    if params['preview'] == False:return


    active_layer = doc.activeNode()
    selected_shapes = []
    
    if active_layer.type() == 'vectorlayer':
        selected_shapes = [shape for shape in active_layer.shapes() if shape.isSelected()]
        # Apply to the selected_shapes
    else:
        print("Error: Current Layer isn't a VectorLayer")
        return

    if selected_shapes:
        shape_count = 0
        for s in selected_shapes:
            if not s:continue
            print("Selected:", s.name())
            #print("data:", s.toSvg())
            qabst = s.absoluteTransformation()
            abst = qtransform_to_svg_transform(qabst)
            # print("abst:", abst)
    
            d_width=0;d_height=0
    
            inv_transf, invertible = s.absoluteTransformation().inverted()
            #inv_transf, invertible = s.transformation().inverted()
    
            local_rect = inv_transf.mapRect(s.boundingBox())
            
            
            x = local_rect.x()
            y = local_rect.y()
            width = local_rect.width()
            height = local_rect.height()


            tx = ty = 0
            svg_txt = s.toSvg()

            match_st = re.search(r'stroke-width="([\d.]+)"', svg_txt)
            match_lc = re.search(r'stroke-linecap="([\w.]+)"', svg_txt)
            match_lj = re.search(r'stroke-linejoin="([\w.]+)"', svg_txt)


            # stroke width padding
            wpad = pt_to_px(0.72,96)# 
            # params['dbg_wpad']=0.53;params['dbg_dpad']=3.05
            test=0
            if test==0 and match_lc and match_lj:
                lcap  = match_lc.group(1)
                ljoin = match_lj.group(1)
                if lcap=="butt"  :params['dbg_wpad']=0.2;params['dbg_dpad']=7.638
                if lcap=="round" :params['dbg_wpad']=0.32;params['dbg_dpad']=4.77199
                if lcap=="square":params['dbg_wpad']=0.7;params['dbg_dpad']=3.08661
                if lcap=="butt" and ljoin=="miter":params['dbg_wpad']=4.8;params['dbg_dpad']=1.27264

                #print(s.name(),"lcap",lcap," _ ", params['dbg_wpad'] ," and ", params['dbg_dpad'] )

            #wpad = wpad*float(match_st.group(1))*0.53#0.53
            wpad = wpad*float(match_st.group(1))*params['dbg_wpad']#0.53

            # Increase wpad then the frame size decrease (become smaller)
            #if params['dimension']==True:wpad = wpad*3.05 #3.05 
            if params['dimension']==True:wpad = wpad*params['dbg_dpad'] #3.05 

            #print("WPAD:",wpad)

            # The case of 30mm rectangle

            # line-cap
            # 30mm butt, x bevel  0.2    7.638  ok
            # 30mm square x bevel,   0.7  2.9  ok
            # 30mm round x all,    0.25  5.7  ok

 
            trans = ""
            match = re.search(r'transform="[^"]*translate\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)"', svg_txt)
            match_mx = re.search(r'transform="matrix\(([^)]+)\)"', svg_txt)

            if match_mx:
                # from matrix
                a, b, c, d, e, f = map(float, match_mx.group(1).split())
                # from bb
                bounds = get_groupshape_bounds(s)
                center = {}
                b_width = b_height = 0
                if bounds:
                    min_x, min_y, max_x, max_y, cx, cy = bounds
                    tx= min_x;ty=min_y
                    center={'x':cx,'y':cy}
                    b_width = abs(min_x - max_x)
                    b_height = abs(min_y - max_y)
                else:
                    center={'x':0,'y':0}

                print("center",center)
                # add stroke paddings

                """
                tx = e + wpad * 0.5 - cx*0.5#cx
                ty = f + wpad * 0.5 + cy*0.5 #+cy
                width  = pt_to_px(b_width,72)-wpad
                height = pt_to_px(b_height,72)-wpad

                """
                tx = e+wpad - cx*0.5
                ty = f+wpad - cx*0.5
                width = pt_to_px(b_width,96)-wpad
                height = pt_to_px(b_height,96)-wpad
                # print(f"translate x: {tx}, y: {ty}")

                tx = tx- wpad*0.5
                ty = ty- wpad*0.5


                trans = f'translate({tx},{ty})'# 40 43


            elif match:
                """
                tx = float(match.group(1))+wpad*0.5
                ty = float(match.group(2))+wpad*0.5
                width = pt_to_px(width,96)-wpad
                height = pt_to_px(height,96)-wpad
                # print(f"translate x: {tx}, y: {ty}")
                trans = f"translate({tx},{ty})"
                """

                tx = float(match.group(1))+wpad
                ty = float(match.group(2))+wpad
                width = pt_to_px(width,96)-wpad
                height = pt_to_px(height,96)-wpad
                # print(f"translate x: {tx}, y: {ty}")

                tx = tx- wpad*0.5
                ty = ty- wpad*0.5
                trans = f"translate({tx},{ty})"

            else:
                print("translate(x, y) notfound")


            if params['size_type'] != 'Sizes':
                print('Set mode:',params['size_type'],params['size_dir'])
                size = get_size(params['size_type'],params['size_dir'])
                width = size['width']
                height = size['height']
                #x = (doc.width()-width)*0.5*0.72 
                #y = (doc.height()-height)*0.5*0.72
    
            #print("Shape:",x,y,width,height)
            #print("Doc wh:",d_width,d_height)

            if params['slice']==True and params['vtotal_w'] == 1 :
                params['vtotal_w'] = width*PT_EQ_1MM
            if params['slice']==True and params['vtotal_h'] == 1 :
                params['vtotal_h'] = height*PT_EQ_1MM


            #matrix = s.absoluteTransformation()
            #matrix = s.transformation()
            #s.setTransformation(Qtransform matrix)
            
            prefix = params['prefix']
            svg_text=draw_cropmarks(shape_count,doc,trans,params,x,y,width,height,prefix)
            #print(svg_text)
            #vector_layers[0].addShapesFromSvg(svg_text)
            active_layer.addShapesFromSvg(svg_text)
    
    
            # Zindex
            view = app.activeWindow().activeView()
            selected_layers = view.selectedNodes()
            
            if doc:
                for node in selected_layers:
                    if node.type() == "vectorlayer":
                        shapes = node.shapes()
                        for shape in shapes:
                            # if shape.isSelected():
                            sname = shape.name()
                            if sname.startswith("tonbo_"): shape.setZIndex(9999) # show or hide
            shape_count = shape_count + 1
    
    
    else:
        print("Error: VectorLayer not found")
    #print(active_layer.toSvg())


def apply_matrix_to_point(x, y, a, b, c, d, e, f):
    new_x = a * x + c * y + e
    new_y = b * x + d * y + f
    return new_x, new_y

def get_groupshape_bounds(krita_shape):
    """
    Return BB and center coordinates of the GroupShape
    Return: (min_x, min_y, max_x, max_y, center_x, center_y)

    bounds = get_groupshape_bounds(krita_shape)
    if bounds:
        min_x, min_y, max_x, max_y, cx, cy = bounds

    """
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')

    def collect_bounds(shape):
        nonlocal min_x, min_y, max_x, max_y
        if shape.type() == 'groupshape':
            for child in shape.children():
                collect_bounds(child)
        else:
            inv_transf, invertible = shape.absoluteTransformation().inverted()
            bbox = inv_transf.mapRect(shape.boundingBox())
            min_x = min(min_x, bbox.x())
            min_y = min(min_y, bbox.y())
            max_x = max(max_x, bbox.x() + bbox.width())
            max_y = max(max_y, bbox.y() + bbox.height())

    collect_bounds(krita_shape)

    if min_x == float('inf'):
        return None  # No shapes in the group

    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    return (min_x, min_y, max_x, max_y, center_x, center_y)



def apply_transform_to_points(transform: QTransform, points: list):
    transformed_points = [transform.map(point[0], point[1]) for point in points]
    return [{"x": p.x(), "y": p.y()} for p in transformed_points]



def qtransform_to_svg_transform(transform: QTransform):
    return f"matrix({transform.m11()} {transform.m12()} {transform.m21()} {transform.m22()} {transform.m31()} {transform.m32()})"


# for single test
if __name__ == "__main__":
    main(params)



