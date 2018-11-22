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
ImportC "/usr/lib/x86_64-linux-gnu/libappindicator3.so.1"
	app_indicator_new.i(id.p-utf8, icon_name.p-utf8, category.l)
	app_indicator_new_with_path.i(id.p-utf8, icon_name.p-utf8, category.l, icon_theme_path.p-utf8)
	app_indicator_build_menu_from_desktop(*indicator, desktop_file.p-utf8, desktop_profile.p-utf8)
	app_indicator_get_attention_icon.i(*indicator)
	app_indicator_get_attention_icon_desc.i(*indicator)
	app_indicator_get_category.l(*indicator)
	app_indicator_get_icon.i(*indicator)
	app_indicator_get_icon_desc.i(*indicator)
	app_indicator_get_icon_theme_path.i(*indicator)
	app_indicator_get_id.i(*indicator)
	app_indicator_get_label.i(*indicator)
	app_indicator_get_label_guide.i(*indicator)
	app_indicator_get_ordering_index.l(*indicator)
	app_indicator_get_status.l(*indicator)
	app_indicator_set_attention_icon(*indicator, icon_name.p-utf8)
	app_indicator_set_attention_icon_full(*indicator, icon_name.p-utf8, icon_desc.p-utf8)
	app_indicator_set_icon(*indicator, icon_name.p-utf8)
	app_indicator_set_icon_full(*indicator, icon_name.p-utf8, icon_desc.p-utf8)
	app_indicator_set_icon_theme_path(*indicator, icon_theme_path.p-utf8)
	app_indicator_set_label(*indicator, label.p-utf8, guide.p-utf8)
	app_indicator_set_menu(*indicator, *menu)
	app_indicator_set_ordering_index(*indicator, ordering_index.l)
	app_indicator_set_status(*indicator, status.l)
EndImport
; IDE Options = PureBasic 5.62 (Linux - x64)
; Folding = -
; EnableXP