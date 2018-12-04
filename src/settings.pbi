EnableExplicit

Enumeration Window
  #Window_Settings
EndEnumeration

Enumeration MenuItem
  #Menu_Settings_Close
EndEnumeration

Enumeration Gadget
  #Gadget_Settings_KeyboardInputDevice_Frame
  #Gadget_Settings_KeyboardInputDevice_List
  #Gadget_Settings_IconTheme_Frame
  #Gadget_Settings_IconTheme_List
  #Gadget_Settings_EnableTrayIcon
  #Gadget_Settings_CreateDesktopFile
  #Gadget_Settings_Save
  #Gadget_Settings_Cancel
EndEnumeration

Procedure OpenSettingsWindow()
  If OpenWindow(#Window_Settings, 0, 0, 500, 320, "Settings", #PB_Window_WindowCentered, WindowID(#Window_Main))
    FrameGadget(#Gadget_Settings_KeyboardInputDevice_Frame, 10, 10, 480, 130, "Keyboard input device")
    ListViewGadget(#Gadget_Settings_KeyboardInputDevice_List, 20, 30, 460, 100)
    
    FrameGadget(#Gadget_Settings_IconTheme_Frame, 10, 150, 480, 60, "Icon theme")
    ComboBoxGadget(#Gadget_Settings_IconTheme_List, 20, 170, 460, 20)
    AddGadgetItem(#Gadget_Settings_IconTheme_List, -1, "bright")
    AddGadgetItem(#Gadget_Settings_IconTheme_List, -1, "dark")
    GadgetToolTip(#Gadget_Settings_IconTheme_List, "Used for application and tray icon")
    
    CheckBoxGadget(#Gadget_Settings_EnableTrayIcon, 10, 220, 460, 20, "Enable tray icon")
    
    ButtonGadget(#Gadget_Settings_CreateDesktopFile, 10, 250, 100, 20, "Create desktop file")
    GadgetToolTip(#Gadget_Settings_CreateDesktopFile, "Create a desktop file in ~/.local/share/applications")
    
    ButtonGadget(#Gadget_Settings_Save, 280, 280, 100, 30, "Save")
    ButtonGadget(#Gadget_Settings_Cancel, 390, 280, 100, 30, "Cancel")
    
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
      config\useTrayIcon = #False
      DisableGadget(#Gadget_Settings_EnableTrayIcon, #True)
      GadgetToolTip(#Gadget_Settings_EnableTrayIcon, "App Indicator not avilable")
    EndIf
    
    SetGadgetText(#Gadget_Settings_IconTheme_List, config\icons)
    SetGadgetState(#Gadget_Settings_EnableTrayIcon, config\useTrayIcon)
    
    Repeat
      Select WaitWindowEvent()
        Case #PB_Event_Menu
          Select EventMenu()
            Case #Menu_Settings_Close
              Break
          EndSelect
        Case #PB_Event_Gadget
          Select EventGadget()
            Case #Gadget_Settings_CreateDesktopFile
              ; Can't use Preferences function as file must be written without BOM
              Protected desktopFile.s = GetHomeDirectory() + ".local/share/applications/keyboard-mapper.desktop"
              Protected file = CreateFile(#PB_Any, desktopFile)
              If IsFile(file)
                WriteStringN(file, "[Desktop Entry]")
                WriteStringN(file, "Comment=" + #Application_Description)
                WriteStringN(file, "Name=" + #Application_Name)
                WriteStringN(file, "Type=Application")
                WriteStringN(file, "Categories=System;")
                WriteStringN(file, "Exec=" + ProgramFilename())
                WriteStringN(file, "Icon=" + appPath + "icons/appicon-" + config\icons + ".png")
                CloseFile(file)
                
                MessageRequester(GetGadgetText(#Gadget_Settings_CreateDesktopFile), "The desktop file has been written to " + desktopFile, #PB_MessageRequester_Info)
              Else
                MessageRequester(GetGadgetText(#Gadget_Settings_CreateDesktopFile), "Can't write desktop file to " + desktopFile, #PB_MessageRequester_Error)
              EndIf
            Case #Gadget_Settings_Save
              If GetGadgetState(#Gadget_Settings_KeyboardInputDevice_List) = -1
                MessageRequester("No keyboard input device selected", "Please selected the input device to use!", #PB_MessageRequester_Error)
                Continue
              EndIf
              
              config\keyboardInputDevice = devicesDir + "/" + GetGadgetText(#Gadget_Settings_KeyboardInputDevice_List)
              config\icons = GetGadgetText(#Gadget_Settings_IconTheme_List)
              config\useTrayIcon = GetGadgetState(#Gadget_Settings_EnableTrayIcon)
              
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
