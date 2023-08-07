from mojo.tools import CallbackWrapper
import vanilla as vui
import AppKit, pprint
import sys
from mojo.UI import AccordionView#PostBannerNotification
from mojo import events
from mojo.extensions import (
    registerExtensionDefaults,
    getExtensionDefault,
    setExtensionDefault
)
extensionName = "ExtensionsSettings"
extensionID = f"com.rafalbuchner.{extensionName}"
extensionKeyStub = extensionID + "."

__defaults__ = {
    extensionKeyStub + "focusedView": 1,
    extensionKeyStub + "registeredDefaults": {"~~~~~~~~~~~~": False}
}

def registerDefaultsToExtensionsSettings(your_extension_ID, defaultsDict):
    registerExtensionDefaults(defaultsDict)
    exst_key = "com.rafalbuchner.ExtensionsSettings.registeredDefaults"
    defaults = getExtensionDefault(exst_key)

    if defaults is None:
        defaults = {}
    if your_extension_ID in defaults.keys():
        del(defaults[your_extension_ID])
    defaults[your_extension_ID] = defaultsDict
    setExtensionDefault(exst_key, defaults)

# def registerDefaultsToExtensionsSettings(your_extension_ID, defaultsDict):
#     registerExtensionDefaults(defaultsDict)
#     defaults = internalGetDefault("registeredDefaults")

#     if defaults is None:
#         defaults = {}
#     if your_extension_ID in defaults.keys():
#         del(defaults[your_extension_ID])
#     defaults[your_extension_ID] = defaultsDict
#     internalSetDefault("registeredDefaults", defaults)

def internalRegisterDefaults():
    registerExtensionDefaults(__defaults__)

def internalGetDefault(key):
    key = extensionKeyStub + key
    return getExtensionDefault(key)


def internalSetDefault(key, value):
    key = extensionKeyStub + key
    setExtensionDefault(key, value)




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
internalRegisterDefaults()

class ExtensionSettingsWindow:
    # 30 * len(__default__)
    def __init__(self, defaults=None, extensionName=None):
        self.loadSettingsDict()

        self.w = vui.FloatingWindow((500, 200), minSize=(500,200), autosaveName=extensionKeyStub+"windowKey")
        searchWidth = 200
        self.w.title = vui.TextBox((10, 10, 180, 22), "Extension's Settings")
        self.w.searchBox = vui.SearchBox((-190, 10, 180, 22),
                                callback=self.searchBoxCallback)
        self.w.box = vui.Box((10,42,-10,-10))
        self.buildSettingsAccordionView()

        self.w.open()

    def searchBoxCallback(self, sender):
        def lookForMatchingEntry(str_entry):
            for entry in searchEntries:
                if entry not in str_entry.lower():
                    return False
            return True

        searchEntries = sender.get().lower().split(" ")
        searchedList = ["Curve Extension", "Stem Plow", "Laser Measure"]
        searchResult = filter(lookForMatchingEntry, searchedList)
        print(searchResult)

    def loadSettingsDict(self):
        # load defaults
        allExtensionDefaults = internalGetDefault("registeredDefaults")
        self.allExtensionDefaults = {eID:defaults[eID+".order"] for eID, defaults in allExtensionDefaults.items()}

    allExtensionDefaults = {}
    def buildSettingsAccordionView(self):
        descriptions = []
        for some_extension_ID, some_extension_defaults in self.allExtensionDefaults.items():
            gridView, height = self.buildSettingsView(some_extension_ID, some_extension_defaults)
            if gridView is None:
                continue
            extensionName = some_extension_defaults[0].split(".")[-2]
            extensionName = camelCaseToSpaced(extensionName)
            descriptions.append(
                dict(
                        label=extensionName,
                        view=gridView, size=height,
                        collapsed=True,
                        canResize=False
                    )
            )
        self.w.box.accordion = AccordionView((0, 0, -0, -0), descriptions)

    settingViews = []

    def buildSettingsView(self, some_extension_ID, some_extension_defaults):
        contents = self.buildSettingItems(some_extension_defaults)

        if len(contents) == 0:
            return None, None

        settingView = vui.GridView(
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
        attrName = some_extension_ID.replace(".", "_") + "_gridView"
        setattr(self, attrName, settingView)
        gridView = getattr(self, attrName)
        self.settingViews.append(gridView)
        height = len(contents)*30+10
        return gridView, height


    def buildSettingItems(self, some_extension_defaults):
        items = []
        for keyEntry in some_extension_defaults:
            key = keyEntry.split(".")[-1]
            if "_" not in keyEntry:
                continue

            if not key.startswith("exst_"):
                continue

            value = None
            title = camelCaseToSpaced(key.split("_")[1]).lower()
            className = key.split("_")[2]
            ClassType = vui.__dict__[className]
            args = ("auto",)
            kwargs = dict(callback=self.objCallback)
            if key.count("_") > 3:
                classArgs = key.split("_")[3:]

            if className == "SegmentedButton":
                args = ("auto", [dict(title=n) for n in classArgs])
                value = getExtensionDefault(keyEntry)

            elif className == "Slider":
                sliderData = getExtensionDefault(keyEntry)
                kwargs.update( dict(maxValue=sliderData.get("maxValue", 100), minValue=sliderData.get("minValue", 0)) )
                # kwargs["callback"] = self.objCallback
                value = getExtensionDefault(keyEntry).get("value")

            elif className == "CheckBox":
                value = getExtensionDefault(keyEntry)
                args  = ("auto", title)
                title = " "

            elif className == "ColorWell":
                color = getExtensionDefault(keyEntry)
                color = convertRGBA_to_NSColor(color)
                args = ("auto",)
                # kwargs = dict(callback=self.objCallback, color=color, colorWellStyle="expanded")
                kwargs.update( dict(color=color, colorWellStyle="expanded") )

            else:
                value = getExtensionDefault(keyEntry)

            obj = ClassType(*args,**kwargs)
            obj._id = keyEntry
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
            some_extension_ID = ".".join(key.split(".")[:-1])
            setExtensionDefault(key, value)
            events.postEvent(some_extension_ID + ".defaultsChanged")


class ExtensionSettings:
    def __init__(self):
        # self.window = ExtensionSettingsWindow()
        events.addObserver(self, "waitForActive", "applicationDidFinishLaunching")

    def waitForActive(self, info):
        events.addObserver(self, "addMenuItem", "applicationDidBecomeActive")

    def addMenuItem(self, info):
        events.removeObserver(self, "applicationDidBecomeActive")
        events.removeObserver(self, "applicationDidFinishLaunching")

        # # check if there is any setting to parse: otherwise do not add window to the menu
        # if not len(self.window.settingViews):
        #     return

        menubar = AppKit.NSApp().mainMenu()

        # RoboFont > Extension Settings...
        title = "Extension Settings…"
        # Find the RoboFont menu
        roboMenu = menubar.itemAtIndex_(0)
        # Get the submenu
        roboSubMenu = roboMenu.submenu()
        # Check if the menu item already exists
        extensionSettingsMenuItem = roboSubMenu.itemWithTitle_(title)

        if not extensionSettingsMenuItem:
            # If it doesn't exist, create a new NSMenuItem with the title "Copy Version Info..." and add it to the menu below the About item
            self.extensionSettingsInfoTarget = CallbackWrapper(self.extensionSettingsInfoCallback)
            extensionSettingsMenuItem = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                title,
                "action:",
                ""
            )
            extensionSettingsMenuItem.setTarget_(self.extensionSettingsInfoTarget)

            itemIdx = 1
            for someItem in roboSubMenu.itemArray():
                if someItem.isSeparatorItem():
                    break
                itemIdx += 1

            roboSubMenu.insertItem_atIndex_(extensionSettingsMenuItem, itemIdx)


    def extensionSettingsInfoCallback(self, sender):
        ExtensionSettingsWindow()
        # self.window.open()



# if __name__ == "__main__" and "RoboFont" in sys.executable:
#     ExtensionSettingsWindow()

# if __name__ == "__main__" and "RoboFont" not in sys.executable:
#     from vanilla.test.testTools import executeVanillaTest
#     executeVanillaTest(ExtensionSettingsWindow, **dict(defaults=__defaults__))
