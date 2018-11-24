EnableExplicit

;- Windows
Enumeration
  #Window_Main
  #Window_EditShortcut
  #Window_KeyRequester
  #Window_Settings
EndEnumeration

;- Menus
Enumeration
  #Menu_Main
EndEnumeration

;- Toolbars
Enumeration
  #Toolbar_Main
EndEnumeration

;- Menu items
Enumeration
  #Menu_Settings
  #Menu_Quit
  #Menu_AddShortcut
  #Menu_EditShortcut
  #Menu_RemoveShortcut
  #Menu_Help
  #Menu_About
  #Menu_EditShortcut_Save
  #Menu_EditShortcut_Cancel
  #Menu_Settings_Close
EndEnumeration

;- Gadgets
Enumeration
  #Gadget_ShortcutList
  #Gadget_EditShortcut_Shortcut_Frame
  #Gadget_EditShortcut_Shortcut
  #Gadget_EditShortcut_Name_Frame
  #Gadget_EditShortcut_Name
  #Gadget_EditShortcut_Action_Frame
  #Gadget_EditShortcut_Action_LaunchApplication
  #Gadget_EditShortcut_Action_LaunchApplication_List
  #Gadget_EditShortcut_Action_ExecuteCommand
  #Gadget_EditShortcut_Action_ExecuteCommand_CommandLine
  #Gadget_EditShortcut_Action_OpenFolder
  #Gadget_EditShortcut_Action_OpenFolder_Path
  #Gadget_EditShortcut_Action_OpenFolder_Browse
  #Gadget_EditShortcut_Action_InputText
  #Gadget_EditShortcut_Action_InputText_Text
  #Gadget_EditShortcut_Save
  #Gadget_EditShortcut_Cancel
  #Gadget_KeyRequester_Text
  #Gadget_KeyRequester_Cancel
  #Gadget_Settings_KeyboardInputDevice_Frame
  #Gadget_Settings_KeyboardInputDevice_List
  #Gadget_Settings_Tray_Frame
  #Gadget_Settings_Tray_Enable
  #Gadget_Settings_Tray_DarkTheme
  #Gadget_Settings_Save
  #Gadget_Settings_Cancel
EndEnumeration

Enumeration
  #Image_AppIcon
  #Image_ApplicationListIcon
EndEnumeration

Enumeration
  #Library_AppIndicator
EndEnumeration

Enumeration
  #TrayIcon_Menu_Show
  #TrayIcon_Menu_Quit
EndEnumeration

Enumeration
  #GTK_ICON_LOOKUP_ALL              = 0; Not gtk-defined, own constant to clearify
  #GTK_ICON_LOOKUP_NO_SVG           = 1
  #GTK_ICON_LOOKUP_FORCE_SVG        = 2
  #GTK_ICON_LOOKUP_USE_BUILTIN      = 4
  #GTK_ICON_LOOKUP_GENERIC_FALLBACK = 8
  #GTK_ICON_LOOKUP_FORCE_SIZE       = 16
EndEnumeration

Enumeration
  #GTK_LICENSE_UNKNOWN
  #GTK_LICENSE_CUSTOM
  #GTK_LICENSE_GPL_2_0
  #GTK_LICENSE_GPL_3_0
  #GTK_LICENSE_LGPL_2_1
  #GTK_LICENSE_LGPL_3_0
  #GTK_LICENSE_BSD
  #GTK_LICENSE_MIT_X11
  #GTK_LICENSE_ARTISTIC
  #GTK_LICENSE_GPL_2_0_ONLY
  #GTK_LICENSE_GPL_3_0_ONLY
  #GTK_LICENSE_LGPL_2_1_ONLY
  #GTK_LICENSE_LGPL_3_0_ONLY
  #GTK_LICENSE_AGPL_3_0
  #GTK_LICENSE_AGPL_3_0_ONLY
EndEnumeration

ImportC "-no-pie"
EndImport

ImportC ""
  gtk_menu_item_new_with_label.i(label.p-utf8)
  g_signal_connect_data.i(*instance, detailed_signal.p-utf8, *c_handler, *data_=0, *destroy_data=0, *connect_flags=0)
  gtk_icon_theme_load_icon(*icon_theme.GtkIconTheme, icon_name.p-utf8, size, flags, *error.GError)
  gtk_about_dialog_new()
  gtk_about_dialog_set_program_name(*about, name.p-utf8)
  gtk_about_dialog_set_version(*about, version.p-utf8)
  gtk_about_dialog_set_copyright(*about, copyright.p-utf8)
  gtk_about_dialog_set_comments(*about, comments.p-utf8)
  gtk_about_dialog_set_license_type(*about, license_type)
  gtk_about_dialog_set_website(*about, website.p-utf8)
  gtk_about_dialog_set_website_label(*about, website_label.p-utf8)
  gtk_about_dialog_set_logo(*about, *logo)
  gtk_about_dialog_add_credit_section(*about, section_name.p-utf8, *people)
  gtk_about_dialog_set_documenters(*about, *documenters)
  gtk_about_dialog_set_authors(*about, *authors)
  gtk_about_dialog_set_translator_credits(*about, translator_credits.p-utf8)
EndImport

Declare.b IsStringFieldInStringField(string1.s, string2.s, separator1.s, separator2.s)
Declare.b StrToBool(string.s)
Declare UpdateListEntry(item, shortcut)

Global editShortcutItem
Global quit.b
Global appIndicator

IncludeFile "desktop-entry.pbi"
IncludeFile "common.pbi"
IncludeFile "editor.pbi"
IncludeFile "input-handler.pbi"
IncludeFile "CLI_Helper.pbi"
IncludeFile "appindicator.pbi"

ProcedureC HandleTrayIconMenuItem(*Widget, item)
  Select item
    Case #TrayIcon_Menu_Show
      HideWindow(#Window_Main, #False)
    Case #TrayIcon_Menu_Quit
      quit = #True
  EndSelect
EndProcedure

Procedure AddGTKMenuItem(menu, item, label.s)
  Protected gtkWidget = gtk_menu_item_new_with_label(label)
  
  g_signal_connect_data(gtkWidget, "activate", @HandleTrayIconMenuItem(), item)
  
  gtk_menu_shell_append_(menu, gtkWidget)
  gtk_widget_show_(gtkWidget)
EndProcedure

Procedure CreateTrayIcon()
  appIndicator = app_indicator_new_with_path("Keyboard Mapper", "appicon-" + config\trayIcon, #APP_INDICATOR_CATEGORY_APPLICATION_STATUS, appPath + "/icons")
  app_indicator_set_status(appIndicator, #APP_INDICATOR_STATUS_ACTIVE)
  
  Protected menu = gtk_menu_new_()
  
  AddGTKMenuItem(menu, #TrayIcon_Menu_Show, "Show window")
  AddGTKMenuItem(menu, #TrayIcon_Menu_Quit, "Quit")
  
  app_indicator_set_menu(appIndicator, menu)
EndProcedure

Procedure UpdateTrayIcon()
  If config\trayIconEnable
    If IsLibrary(#Library_AppIndicator)
      If appIndicator
        app_indicator_set_icon(appIndicator, "appicon-" + config\trayIcon)
      Else
        CreateTrayIcon()
      EndIf
    Else
      MessageRequester("Keyboard Mapper", "Can't add tray icon: App Indicator not available!", #PB_MessageRequester_Error)
      
      config\trayIconEnable = #False
      SaveConfig()
    EndIf
  EndIf
EndProcedure

Procedure UpdateListEntry(item, shortcutKey)
  Protected shortcut.Shortcut = shortcuts(Str(shortcutKey))
  
  If item = -1
    AddGadgetItem(#Gadget_ShortcutList, -1, shortcut\name)
    item = CountGadgetItems(#Gadget_ShortcutList) - 1
  Else
    SetGadgetItemText(#Gadget_ShortcutList, item, shortcut\name)
  EndIf
  
  Protected actionDetails.s
  
  Select shortcut\action
    Case #Action_LaunchApplication
      Protected desktopEntry.DesktopEntry
      
      ReadDesktopFile(shortcut\actionData, desktopEntry)
      actionDetails = desktopEntry\name
    Default
      actionDetails = shortcut\actionData
  EndSelect
  
  SetGadgetItemText(#Gadget_ShortcutList, item, ActionToString(shortcut\action) + ": " + actionDetails, 1)
  SetGadgetItemText(#Gadget_ShortcutList, item, Str(shortcutKey), 2)
  SetGadgetItemData(#Gadget_ShortcutList, item, shortcutKey)
EndProcedure

Procedure UpdateMainGadgetSizes()
  ResizeGadget(#Gadget_ShortcutList, 10, 10, WindowWidth(#Window_Main) - 20, WindowHeight(#Window_Main) - ToolBarHeight(#Toolbar_Main) - MenuHeight() - 20)
EndProcedure

Procedure OpenSettingsWindow()
  If OpenWindow(#Window_Settings, 0, 0, 500, 280, "Settings", #PB_Window_WindowCentered, WindowID(#Window_Main))
    FrameGadget(#Gadget_Settings_KeyboardInputDevice_Frame, 10, 10, 480, 130, "Keyboard input device")
    ListViewGadget(#Gadget_Settings_KeyboardInputDevice_List, 20, 30, 460, 100)
    
    FrameGadget(#Gadget_Settings_Tray_Frame, 10, 150, 480, 80, "Tray icon")
    CheckBoxGadget(#Gadget_Settings_Tray_Enable, 20, 170, 460, 20, "Enable")
    CheckBoxGadget(#Gadget_Settings_Tray_DarkTheme, 20, 200, 460, 20, "Use for dark theme")
    
    ButtonGadget(#Gadget_Settings_Save, 280, 240, 100, 30, "Save")
    ButtonGadget(#Gadget_Settings_Cancel, 390, 240, 100, 30, "Cancel")
    
    AddKeyboardShortcut(#Window_Settings, #PB_Shortcut_Escape, #Menu_Settings_Close)
    
    DisableWindow(#Window_Main, #True)
    DisableWindow(#Window_Settings, #False); With QT5 the child window is disabled after disabling the parent
    
    Protected devicesDir.s = "/dev/input/by-id"
    Protected dir = ExamineDirectory(#PB_Any, devicesDir, "")
    If IsDirectory(dir)
      While NextDirectoryEntry(dir)
        If DirectoryEntryType(dir) = #PB_DirectoryEntry_File
          Protected filename.s = DirectoryEntryName(dir)
          
          AddGadgetItem(#Gadget_Settings_KeyboardInputDevice_List, -1, filename)
          
          If devicesDir + "/" + filename = config\keyboardInputDevice
            SetGadgetState(#Gadget_Settings_KeyboardInputDevice_List, CountGadgetItems(#Gadget_Settings_KeyboardInputDevice_List) - 1)
          EndIf
        EndIf
      Wend
      FinishDirectory(dir)
    EndIf
    
    If Not IsLibrary(#Library_AppIndicator)
      config\trayIconEnable = #False
      DisableGadget(#Gadget_Settings_Tray_Enable, #True)
      GadgetToolTip(#Gadget_Settings_Tray_Frame, "App Indicator not avilable")
    EndIf
    
    SetGadgetState(#Gadget_Settings_Tray_Enable, config\trayIconEnable)
    
    If config\trayIcon = "bright"
      SetGadgetState(#Gadget_Settings_Tray_DarkTheme, #True)
    Else
      SetGadgetState(#Gadget_Settings_Tray_DarkTheme, #False)
    EndIf
    
    If config\trayIconEnable
      DisableGadget(#Gadget_Settings_Tray_DarkTheme, #False)
    Else
      DisableGadget(#Gadget_Settings_Tray_DarkTheme, #True)
    EndIf
    
    Repeat
      Select WaitWindowEvent()
        Case #PB_Event_Menu
          Select EventMenu()
            Case #Menu_Settings_Close
              Break
          EndSelect
        Case #PB_Event_Gadget
          Select EventGadget()
            Case #Gadget_Settings_Tray_Enable
              If GetGadgetState(#Gadget_Settings_Tray_Enable)
                DisableGadget(#Gadget_Settings_Tray_DarkTheme, #False)
              Else
                DisableGadget(#Gadget_Settings_Tray_DarkTheme, #True)
              EndIf
            Case #Gadget_Settings_Save
              If GetGadgetState(#Gadget_Settings_KeyboardInputDevice_List) = -1
                MessageRequester("No keyboard input device selected", "Please selected the input device to use!", #PB_MessageRequester_Error)
                Continue
              EndIf
              
              config\keyboardInputDevice = devicesDir + "/" + GetGadgetText(#Gadget_Settings_KeyboardInputDevice_List)
              config\trayIconEnable = GetGadgetState(#Gadget_Settings_Tray_Enable)
              
              If GetGadgetState(#Gadget_Settings_Tray_DarkTheme)
                config\trayIcon = "bright"
              Else
                config\trayIcon = "dark"
              EndIf
              
              SaveConfig()
              RestartInputEventListener()
              UpdateTrayIcon()
              Break
            Case #Gadget_Settings_Cancel
              Break
          EndSelect
        Case #PB_Event_CloseWindow
          If EventWindow() = #Window_Settings
            Break
          EndIf
      EndSelect
    ForEver
    
    CloseWindow(#Window_Settings)
    DisableWindow(#Window_Main, #False)
  EndIf
EndProcedure

Procedure ShowAbout()
  Protected *about
  
  Protected Dim AboutAuthors.s(1)
  AboutAuthors(0) = StringToUtf8("Programie")
  
  *about = gtk_about_dialog_new()
  gtk_window_set_transient_for_(*about, WindowID(#Window_Main))
  gtk_about_dialog_set_program_name(*about, "Keyboard Mapper")
  gtk_about_dialog_set_version(*about, "v1.0")
  gtk_about_dialog_set_copyright(*about, Chr($A9) + " by Michael Wieland (Programie)")
  gtk_about_dialog_set_comments(*about, "A tool for Linux desktops to map keys of a dedicated keyboard to specific actions.")
  gtk_about_dialog_set_license_type(*about, #GTK_LICENSE_MIT_X11)
  gtk_about_dialog_set_website(*about, "https://selfcoders.com")
  gtk_about_dialog_set_website_label(*about, "Website")
  gtk_about_dialog_set_authors(*about, @AboutAuthors())
  
  If IsImage(#Image_AppIcon)
    Protected image = CopyImage(#Image_AppIcon, #PB_Any)
    If IsImage(image)
      ResizeImage(image, 128, 128)
      gtk_about_dialog_set_logo(*about, ImageID(image))
      FreeImage(image)
    EndIf
  EndIf
  
  gtk_dialog_run_(*about)
  gtk_widget_destroy_(*about)
EndProcedure

Procedure UpdateMenuItems()
  Protected item = GetGadgetState(#Gadget_ShortcutList)
  Protected itemFound.b
  
  If item = -1
    itemFound = #False
  Else
    itemFound = #True
  EndIf
  
  DisableMenuItem(#Menu_Main, #Menu_EditShortcut, Invert(itemFound))
  DisableMenuItem(#Menu_Main, #Menu_RemoveShortcut, Invert(itemFound))
  DisableToolBarButton(#Toolbar_Main, #Menu_EditShortcut, Invert(itemFound))
  DisableToolBarButton(#Toolbar_Main, #Menu_RemoveShortcut, Invert(itemFound))
EndProcedure

Define defaultConfigDir.s = GetHomeDirectory() + ".config/keyboard-mapper"
Define startHidden.b = #False

CLI_AddOption("c", "config-dir", #True , "path", "path to the config dir (default: " + defaultConfigDir + ")")
CLI_AddOption("H", "hidden", #False, "", "start hidden")
CLI_AddOption("h", "help", #False, "", "show this help message")

CLI_ScanCommandline()

If CLI_HasOption("help")
  CLI_Usage()
  End
EndIf

If CLI_HasOption("config-dir")
  configDir = CLI_GetOptionValue("config-dir")
Else
  configDir = defaultConfigDir
EndIf

If CLI_HasOption("hidden")
  startHidden = #True
EndIf

CreateDirectory(configDir)

configFile = configDir + "/config.ini"
shortcutsFile = configDir + "/shortcuts.ini"

LoadConfig()
LoadShortcutsFromFile()

gtk_init_(0, "")

RestartInputEventListener()

UsePNGImageDecoder()

If LoadImage(#Image_AppIcon, appPath + "/icons/appicon-dark.png")
  gtk_window_set_default_icon_(ImageID(#Image_AppIcon))
EndIf

If OpenWindow(#Window_Main, 0, 0, 600, 400, "Keyboard Mapper", #PB_Window_MaximizeGadget | #PB_Window_MinimizeGadget | #PB_Window_ScreenCentered | #PB_Window_Invisible)
  If CreateMenu(#Menu_Main, WindowID(#Window_Main))
    MenuTitle("File")
    MenuItem(#Menu_Settings, "Settings...")
    MenuBar()
    MenuItem(#Menu_Quit, "Quit")
    
    MenuTitle("Edit")
    MenuItem(#Menu_AddShortcut, "Add shortcut...")
    MenuItem(#Menu_EditShortcut, "Edit shortcut...")
    MenuItem(#Menu_RemoveShortcut, "Remove shortcut")
    
    MenuTitle("Help")
    MenuItem(#Menu_Help, "Help" + Chr(9) + "F1")
    MenuBar()
    MenuItem(#Menu_About, "About")
  EndIf
  
  If CreateToolBar(#Toolbar_Main, WindowID(#Window_Main))
    ToolBarStandardButton(#Menu_AddShortcut, #PB_ToolBarIcon_New)
    ToolBarStandardButton(#Menu_EditShortcut, #PB_ToolBarIcon_Properties)
    ToolBarStandardButton(#Menu_RemoveShortcut, #PB_ToolBarIcon_Delete)
    
    ToolBarToolTip(#Toolbar_Main, #Menu_AddShortcut, "Add shortcut")
    ToolBarToolTip(#Toolbar_Main, #Menu_EditShortcut, "Edit shortcut")
    ToolBarToolTip(#Toolbar_Main, #Menu_RemoveShortcut, "Remove shortcut")
  EndIf
  
  ListIconGadget(#Gadget_ShortcutList, 10, 10, 0, 0, "Name", 200, #PB_ListIcon_FullRowSelect | #PB_ListIcon_GridLines)
  AddGadgetColumn(#Gadget_ShortcutList, 1, "Action", 300)
  AddGadgetColumn(#Gadget_ShortcutList, 2, "Key", 100)
  
  UpdateTrayIcon()
  UpdateMainGadgetSizes()
  UpdateMenuItems()
  
  ForEach shortcuts()
    UpdateListEntry(-1, Val(MapKey(shortcuts())))
  Next
  
  HideWindow(#Window_Main, startHidden)
  
  Repeat
    Select WaitWindowEvent(10)
      Case #PB_Event_Menu
        Select EventMenu()
          Case #Menu_Settings
            OpenSettingsWindow()
          Case #Menu_Quit
            Break
          Case #Menu_AddShortcut
            EditShortcut(-1)
          Case #Menu_EditShortcut
            Define item = GetGadgetState(#Gadget_ShortcutList)
            If item <> -1
              EditShortcut(item)
            EndIf
          Case #Menu_RemoveShortcut
            Define item = GetGadgetState(#Gadget_ShortcutList)
            If item <> -1
              DeleteMapElement(shortcuts(), Str(GetGadgetItemData(#Gadget_ShortcutList, item)))
              RemoveGadgetItem(#Gadget_ShortcutList, item)
              SaveShortcutsToFile()
            EndIf
          Case #Menu_Help
            RunProgram("xdg-open", "https://gitlab.com/Programie/keyboard-mapper", "")
          Case #Menu_About
            ShowAbout()
        EndSelect
      Case #PB_Event_Gadget
        Select EventGadget()
          Case #Gadget_ShortcutList
            UpdateMenuItems()
            
            Select EventType()
              Case #PB_EventType_LeftDoubleClick
                Define item = GetGadgetState(#Gadget_ShortcutList)
                If item <> -1
                  EditShortcut(item)
                EndIf
            EndSelect
        EndSelect
      Case #PB_Event_SizeWindow
        UpdateMainGadgetSizes()
      Case #PB_Event_CloseWindow
        If EventWindow() = #Window_Main
          If config\trayIconEnable
            HideWindow(#Window_Main, #True)
          Else
            Break
          EndIf
        EndIf
    EndSelect
  Until quit
EndIf

If IsThread(inputEventListenerThread)
  KillThread(inputEventListenerThread)
EndIf
