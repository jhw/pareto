def grid_layout(charts,
                pagewidth=24,
                heightratio=0.75):
    x, y, widgets = 0, 0, []
    for row in charts:
        width=int(pagewidth/len(row))
        height=int(heightratio*width)
        for chart in row:
            widget={"type": "metric",
                    "x": x,
                    "y": y,
                    "width": width,
                    "height": height,
                    "properties": chart}
            widgets.append(widget)
            x+=width
        y+=height
        x=0 # NB reset
    return {"widgets": widgets}

