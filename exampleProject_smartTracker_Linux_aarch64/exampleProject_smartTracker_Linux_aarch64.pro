
CONFIG += c++11 console
CONFIG -= app_bundle
CONFIG -= qt

TEMPLATE = app

TARGET = exampleProject_smartTracker_Linux_aarch64

SOURCES += \
        main.cpp

HEADERS += include/bt_basic_types.h \
    include/bt_structs_if.h \
    include/ethernetAPI_if.h \
    include/itl_if.h \
    include/ethernet_API_basicTypes.h

unix|win32: LIBS += -L$$PWD/libs/ -lethernetAPI

INCLUDEPATH += $$PWD/libs
DEPENDPATH += $$PWD/libs

unix:!macx: LIBS += -L$$PWD/libs/ -litl

INCLUDEPATH += $$PWD/libs
DEPENDPATH += $$PWD/libs

unix:!macx: LIBS += -L$$PWD/libs/ -lethernetAPI

INCLUDEPATH += $$PWD/libs
DEPENDPATH += $$PWD/libs
