;-------------- FILE: appindicator.gir --------------

; ATTENTION: instances of gulong/ulong/long will be translated to
; a INTEGER/.i. This is right on Linux but probably should be a
; LONG/.l on Windows. If you are brave enough, take a look at
; the TypeTranslator class and the attribute c_types, which
; contains the translation table. There you can fix it.

;- NAMESPACE: AppIndicator from "libappindicator.so.1"

Enumeration ; IndicatorStatus
	#APP_INDICATOR_STATUS_PASSIVE = 0
	#APP_INDICATOR_STATUS_ACTIVE = 1
	#APP_INDICATOR_STATUS_ATTENTION = 2
EndEnumeration

Enumeration ; IndicatorCategory
	#APP_INDICATOR_CATEGORY_APPLICATION_STATUS = 0
	#APP_INDICATOR_CATEGORY_COMMUNICATIONS = 1
	#APP_INDICATOR_CATEGORY_SYSTEM_SERVICES = 2
	#APP_INDICATOR_CATEGORY_HARDWARE = 3
	#APP_INDICATOR_CATEGORY_OTHER = 4
EndEnumeration

CompilerIf Defined(AppIndicatorIndicatorClass, #PB_Structure)
CompilerElse
Structure AppIndicatorIndicatorClass
	*parent_class
	*new_icon
	*new_attention_icon
	*new_status
	*new_icon_theme_path
	*new_label
	*connection_changed
	*scroll_event
	*app_indicator_reserved_ats
	*fallback
	*unfallback
	*app_indicator_reserved_1
	*app_indicator_reserved_2
	*app_indicator_reserved_3
	*app_indicator_reserved_4
	*app_indicator_reserved_5
	*app_indicator_reserved_6
EndStructure
CompilerEndIf

CompilerIf Defined(AppIndicatorIndicatorPrivate, #PB_Structure)
CompilerElse
Structure AppIndicatorIndicatorPrivate
EndStructure
CompilerEndIf

Prototype.i app_indicator_new_with_path(id.p-utf8, icon_name.p-utf8, category.l, icon_theme_path.p-utf8)
Prototype app_indicator_set_icon(*indicator, icon_name.p-utf8)
Prototype app_indicator_set_status(*indicator, status.l)
Prototype app_indicator_set_menu(*indicator, *menu)

If OpenLibrary(#Library_AppIndicator, "libappindicator3.so.1")
  Global app_indicator_new_with_path.app_indicator_new_with_path = GetFunction(#Library_AppIndicator, "app_indicator_new_with_path")
  Global app_indicator_set_icon.app_indicator_set_icon = GetFunction(#Library_AppIndicator, "app_indicator_set_icon")
  Global app_indicator_set_status.app_indicator_set_status = GetFunction(#Library_AppIndicator, "app_indicator_set_status")
  Global app_indicator_set_menu.app_indicator_set_menu = GetFunction(#Library_AppIndicator, "app_indicator_set_menu")
EndIf