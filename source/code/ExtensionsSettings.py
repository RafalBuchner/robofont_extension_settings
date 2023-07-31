
import vanilla as vui
import AppKit, pprint
import sys
from mojo.UI import AccordionView
from mojo import events
from mojo.extensions import (
    registerExtensionDefaults,
    getExtensionDefault,
    setExtensionDefault
)
extensionName = "ExtensionsSettings"
extensionID = f"com.rafalbuchner.{extensionName}"
extensionKeyStub = extensionID + "."

__defaults__ = {}

def registerDefaultsToExtensionsSettings(extensionID, defaultsDict):
    setExtensionDefault(extensionID, defaultsDict)


def internalRegisterDefaults():
    registerExtensionDefaults(__defaults__)

def internalGetDefault(key):
    key = extensionKeyStub + key
    return getExtensionDefault(key)

def internalSetDefault(key, value):
    key = extensionKeyStub + key
    setExtensionDefault(key, value)


internalRegisterDefaults()

def camelCaseToSpaced(txt):
    return ''.join(map(lambda x: x if x.islower() else " "+x, txt))

def convertRGBA_to_NSColor(color):
    if isinstance(color, AppKit.NSColor):
        return color
    return AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(*color)

def convertNSColor_to_RGBA(color):
    color = color.colorUsingColorSpace_(AppKit.NSColorSpace.genericRGBColorSpace())
    r = color.redComponent()
    g = color.greenComponent()
    b = color.blueComponent()
    a = color.alphaComponent()
    return (r, g, b, a)


# internalSetDefault("visualisationSize_Slider_int", dict(minValue=0,maxValue=8000,value=1600))


class ExtensionSettingsView:
    # 30 * len(__default__)
    def __init__(self, defaults=None, extensionName=None):
        contents = self.buildSettingItems(__defaults__)
        self.gridView = vui.GridView(
            (10, 10, -10, -10),
            contents=contents,
            rowSpacing=10,
            rowPadding=(0, 0),
            rowPlacement="top",
            rowAlignment="firstBaseline",
            columnDescriptions=[
                dict(
                    columnPlacement="trailing",
                    width=200
                ),
                dict(
                    columnPlacement="leading",
                    width=300
                )
            ],
            columnSpacing=10,
            columnPadding=(0, 0),
            columnPlacement="leading",

        )
        descriptions = [
            dict(
                    label=camelCaseToSpaced(extensionName),
                    view=self.gridView, size=30 * len(defaults),
                    collapsed=True,
                    canResize=False
                )
            ]
        self.w = vui.Window((500, 200), minSize=(500,200))
        searchWidth = 200
        self.w.title = vui.TextBox((10, 10, 180, 22), "Extension's Settings")
        self.w.searchBox = vui.SearchBox((-190, 10, 180, 22),
                                callback=self.searchBoxCallback)
        self.w.box = vui.Box((10,42,-10,-10))
        self.w.box.accordion = AccordionView((0, 0, -0, -0), descriptions)
        self.w.open()

    def searchBoxCallback(self, sender):
        searchEntries = sender.get().lower().split(" ")
        searchedList = ["Curve Extension", "Stem Plow", "Laser Measure"]
        def lookForMatchingEntry(str_entry):
            for entry in searchEntries:
                if entry not in str_entry.lower():
                    return False
            return True
        searchResult = filter(lookForMatchingEntry, searchedList)

        print(list(searchResult))


    def buildSettingItems(self, __defaults__):
        items = []
        for keyEntry in __defaults__:
            key = keyEntry.split(".")[-1]
            if "_" not in keyEntry:
                continue

            value = None
            title = camelCaseToSpaced(key.split("_")[0]).lower()
            className = key.split("_")[1]
            ClassType = vui.__dict__[className]
            args = ("auto",)
            kwargs = dict(callback=self.objCallback)

            if key.count("_") > 2:
                classArgs = key.split("_")[2:]

            if className == "SegmentedButton":
                args = ("auto", [dict(title=n) for n in classArgs])
                value = internalGetDefault(key)

            elif className == "Slider":
                sliderData = internalGetDefault(key)
                print(sliderData)
                kwargs = dict(maxValue=sliderData.get("maxValue", 100), minValue=sliderData.get("minValue", 0))
                kwargs["callback"] = self.objCallback
                value = internalGetDefault(key).get("value")

            elif className == "CheckBox":
                value = internalGetDefault(key)
                args  = ("auto", title)
                title = " "

            elif className == "ColorWell":
                color = internalGetDefault(key)
                color = convertRGBA_to_NSColor(color)
                args = ("auto",)
                kwargs = dict(callback=self.objCallback, color=color, colorWellStyle="expanded")

            else:
                value = internalGetDefault(key)

            obj = ClassType(*args,**kwargs)
            obj._id = key
            if value is not None:
                obj.set(value)
            setattr(self, key, obj)
            i = dict(
                title=title,
                obj=obj
            )

            items.append(i)

        contents = []
        for item in items:
            title, obj = item["title"], item["obj"]
            titleObj = vui.TextBox("auto", title)
            setattr(self, title.replace(" ","_")+"_TextBox", obj)
            contents.append(dict(cells=[dict(view=titleObj), dict(view=obj)]))

        return contents

    def objCallback(self, sender):
        className = sender.__class__.__name__
        value = sender.get()
        key = sender._id
        assingValue = True

        if key.endswith("_int"):
            try:
                value = int(value)
            except:
                import traceback
                print("wasn't able to assign determine value")
                print(traceback.format_exc)
                assingValue = False

        if className == "CheckBox":
            value = bool(value)

        elif className == "ColorWell":
            value = convertNSColor_to_RGBA(value)

        elif className == "Slider":
            obj = sender.getNSSlider()
            value = dict(
                    minValue=obj.minValue(),
                    value=value,
                    maxValue=obj.maxValue()
                )

        if assingValue:

            internalSetDefault(key, value)
            events.postEvent(extensionID + ".defaultsChanged")
            print("assigned")


if __name__ == "__main__" and "RoboFont" in sys.executable:
    ExtensionSettingsView(__defaults__, extensionName)

if __name__ == "__main__" and "RoboFont" not in sys.executable:
    from vanilla.test.testTools import executeVanillaTest
    executeVanillaTest(ExtensionSettingsView, **dict(defaults=__defaults__))
