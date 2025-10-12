## VectorGuideMarks plug-in - Trim,Grid and Dimension
v0.5  
This plugin can:

- This plugin create trimmark (crop-marks) on selected **Vector shapes**
- Also make a grid for a layout, a comic-strip, a chart or text  
- It aims to produce output SVG that can be edited in Affinity Designer, InkScape and Adobe Illustrator  
- Unit = mm/px/inch, Bleed = 3mm  
- Support Dimension Lines
- Support Modular Grid (Also rounded rectangles)
- Display Text capacity information(for Asian typesetting)

### How to use

1. Create a **Vector Layer, and create a shape**  
2. Select the shape  
3. From Menu, Tools > Scripts > Create Cropmarks...  
4. Choose preset (from many paper sizes) or Free mode (The shape should have no transform)  

### References

- [Paper size](https://en.wikipedia.org/wiki/Paper_size)  
- [Crop marks](https://en.wikipedia.org/wiki/Printing#Crop_marks)  
- [Registration](https://en.wikipedia.org/wiki/Printing_registration)  
- [Bleed (Printing)](https://en.wikipedia.org/wiki/Bleed_(printing))  
- [トンボ (印刷)](https://ja.wikipedia.org/wiki/トンボ_(印刷))  

### Preset

- All: All Preset  
- US  
- Europ  
- India  
- Asia  
- Japan  
- Card  
- Refil  
- Photo  
- Envelope  
- Free: Make the marks on selected shapes  

### Direction

Vertical, Horizontal, Frame  

### Grid

Create grid for multipurpose feature  
It can set numbers of Row and Col, and their spacing  
## Grid Size Control Behavior

- **When `ignore_shape` is no-checked(default)`:**
  - The shape or preset size becomes the absolute reference for drawing.
  - Changing `unit` or `division` will not affect the total size.
  - Instead, `unit` values are automatically recalculated to fit within the fixed shape size.
  - This mode ensures that the layout conforms strictly to the preset dimensions.

- **When `ignore_shape` is checked`:**
  - The user has full control over the grid dimensions.
  - Changing `unit`, `division`, or `total` size directly affects the drawing size.
  - This mode is ideal for custom layouts or flexible grid configurations.
  - The shape size is ignored, allowing free adjustment of all parameters.


### Info
A following info displayed

### The list of the preset paper sizes

- A1: (594.54mm x 841mm)  
- A2: (420.53mm x 595mm)  
- A3: (297.27mm x 421mm)  
- A4: (210.27mm x 297mm)  
- A5: (148.63mm x 210mm)  
- A6: (105.13mm x 149mm)  
- A7: (74.32mm x 105mm)  
- B1: (707.05mm x 1000mm)  
- B2: (500.03mm x 707mm)  
- B3: (353.52mm x 500mm)  
- B4: (250.02mm x 354mm)  
- B5: (176.76mm x 250mm)  
- B6: (125.01mm x 177mm)  
- B8: (62.51mm x 88mm)  
- B1(JIS): (728.05mm x 1030mm)  
- B2(JIS): (515.03mm x 728mm)  
- B3(JIS): (364.02mm x 515mm)  
- B4(JIS): (257.52mm x 364mm)  
- B5(JIS): (182.01mm x 258mm)  
- B6(JIS): (128.76mm x 182mm)  
- D1(GB): (597.04mm x 889mm)  
- D2(GB): (444.53mm x 597mm)  
- D3(GB): (298.52mm x 445mm)  
- D4(GB): (222.26mm x 299mm)  
- D5(GB): (149.26mm x 222mm)  
- D6(GB): (111.13mm x 149mm)  
- D7(GB): (74.63mm x 111mm)  
- HBxWA5: (148.63mm x 210mm)  
- Bible: (95.01mm x 170mm)  
- Narrow: (80.0mm x 170mm)  
- Mini6: (76.0mm x 126mm)  
- Mini5: (61.0mm x 105mm)  
- M5: (62.0mm x 105mm)  
- BusinessCard_JP: (91.0mm x 55mm)  
- BusinessCard_US: (89.0mm x 51mm)  
- BusinessCard_EU: (85.01mm x 55mm)  
- TradingCard_Standard: (63.0mm x 88mm)  
- TradingCard_Small: (59.0mm x 86mm)  
- CreditCard_JIS: (85.61mm x 54mm)  
- Postcard_JP: (100.0mm x 148mm)  
- ShopCard: (85.01mm x 54mm)  
- Archana_Size: (70.01mm x 120mm)  
- Tanzaku_b2: (257.02mm x 728mm)  
- Tanzaku_b3: (182.01mm x 515mm)  
- Porker_Size: (63.0mm x 89mm)  
- Bridge_Size: (58.0mm x 89mm)  
- Shiori: (40.0mm x 125mm)  
- Letter_US: (215.91mm x 279mm)  
- Legal_US: (215.91mm x 356mm)  
- Tabloid_US: (279.42mm x 432mm)  
- Executive_US: (184.16mm x 267mm)  
- Statement_US: (139.71mm x 216mm)  
- Ledger_US: (431.83mm x 279mm)  
- ANSI_A: (216.01mm x 279mm)  
- ANSI_B: (279.02mm x 432mm)  
- ANSI_C: (432.03mm x 559mm)  
- ANSI_D: (559.04mm x 864mm)  
- ANSI_E: (864.06mm x 1118mm)  
- Photo_L: (89.0mm x 127mm)  
- Photo_2L: (127.01mm x 178mm)  
- Photo_KG: (102.01mm x 152mm)  
- Photo_6P: (203.01mm x 254mm)  
- Photo_4P: (254.02mm x 305mm)  
- Photo_8P: (165.01mm x 216mm)  
- Photo_4x6in: (101.61mm x 152mm)  
- Photo_5x7in: (127.01mm x 178mm)  
- Photo_8x10in: (203.21mm x 254mm)  
- Photo_8.5x11in: (215.91mm x 279mm)  
- Photo_11x14in: (279.42mm x 356mm)  
- Photo_16x20in: (406.43mm x 508mm)  
- Photo_20x24in: (508.03mm x 610mm)  
- Photo_10x15cm: (100.0mm x 150mm)  
- Photo_13x18cm: (130.01mm x 180mm)  
- Photo_15x20cm: (150.01mm x 200mm)  
- Photo_18x24cm: (180.01mm x 240mm)  
- Photo_20x30cm: (200.01mm x 300mm)  
- Photo_30x40cm: (300.02mm x 400mm)  
- C4: (229.28mm x 324mm)  
- C5: (162.09mm x 229mm)  
- C6: (114.64mm x 162mm)  
- Chou3: (120.01mm x 235mm)  
- Chou4: (90.01mm x 205mm)  
- Chou2: (119.01mm x 277mm)  
- Kaku2: (240.02mm x 332mm)  
- Kaku3: (216.01mm x 277mm)  
- Kaku0: (287.02mm x 382mm)  
- Kiku 1-cut: (636.04mm x 939mm)  
- Kiku 2-cut: (469.03mm x 636mm)  
- Kiku 4-cut: (318.02mm x 469mm)  
- Kiku 8-cut: (234.02mm x 318mm)  
- Kiku 16-cut: (159.01mm x 234mm)  
- Kiku 32-cut: (117.01mm x 159mm)  
- Shiroku 1-fold: (788.05mm x 1091mm)  
- Shiroku 2-fold: (545.03mm x 788mm)  
- Shiroku 4-fold: (394.02mm x 545mm)  
- Shiroku 8-fold: (273.02mm x 394mm)  
- Shiroku 16-fold: (197.01mm x 273mm)  
- Shiroku 32-fold: (136.01mm x 197mm)  
- Foolscap: (203.01mm x 330mm)  
- Legal_IN: (215.01mm x 345mm)  
- Demi: (445.03mm x 572mm)  
- Quarto: (229.01mm x 279mm)


### Special Thanks 
A following plugin helped me for check and debugging to the Krita internal SVG data.  
[Krita-ShapesAndLayers-Plugin](https://github.com/KnowZero/Krita-ShapesAndLayers-Plugin)
