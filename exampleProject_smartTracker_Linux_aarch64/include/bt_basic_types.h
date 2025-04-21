/**************************************************************************************

      II    N     N     N     N      OOOO      SSSSS     EEEEE    N     N    TTTTTTT
     II    NNN   N     NNN   N    OO    OO    S         E        NNN   N       T
    II    N NN  N     N NN  N    OO    OO    SSSSS     EEE      N NN  N       T
   II    N  NN N     N  NN N    OO    OO        S     E        N  NN N       T
  II    N    NN     N    NN      OOOO      SSSSS     EEEEE    N    NN       T
                       copyright (c) 2011-2018, InnoSenT GmbH
                                 all rights reserved

***************************************************************************************

    filename:		bt_basic_types.h
    brief:          basic track internal used types
    creation:		08.02.2018
    author:			Jonas Kubo
    version:		v1.0
    last edit:
    last editor:
    change:

***************************************************************************************


**************************************************************************************/


#ifndef INCLUSION_GUARDS_BT_BASIC_TYPES_H
#define INCLUSION_GUARDS_BT_BASIC_TYPES_H

/**************************************************************************************
  includes
**************************************************************************************/
#include <limits.h>
#include <float.h>
#include <stddef.h>


/**************************************************************************************
   cross project standard definitions
**************************************************************************************/

#define ON_I				(1)
#define OFF_I				(0)
#if !defined(TRUE_I)
#define TRUE_I				(1)
#endif
#if !defined(FALSE_I)
#define	FALSE_I				(0)
#endif
#define ENABLE_I				(1)
#define DISABLE_I			(0)
#define HIGH_I				(1)
#define LOW_I				(0)
#define START_I				(1)
#define STOP_I				(0)

#if !defined(C0_I)
#define C0_I					(299792458.0f)
#endif
#if !defined(PI_I)
#define PI_I					(3.14159265f)
#endif
#if !defined(DEG2RAD_I)
#define DEG2RAD_I               (0.01745329252f)    /* (PI_I/180.0f) */
#endif
#if !defined(RAD2DEG_I)
#define RAD2DEG_I               (57.29577951f)      /* (180.0f/PI_I) */
#endif
#if !defined(KMH2MPS_I)
#define KMH2MPS_I               (0.2777777777f)     /* (1.0f/3.6f) */
#endif
#if !defined(MPS2KMH_I)
#define MPS2KMH_I             (3.6f)
#endif
#if !defined(NEG_KMH2MPS_I)
#define NEG_KMH2MPS_I         (-KMH2MPS_I)
#endif

#define EQUALS_I				==
#define EQUALS_NOT_I			!=
#define AND_I				&&
#define OR_I					||
#define BIT_AND_I             &
#define BIT_OR_I              |
#ifndef NULL_I
#ifdef __cplusplus
#define NULL_I    0
#else
#define NULL_I    ((void *)0)
#endif
#endif


/**************************************************************************************
  define 8 bit signed/unsigned types & constants
**************************************************************************************/

#if SCHAR_MAX == 127 || SCHAR_MAX == 32767
/** 8bit signed type */
typedef  signed char sint8_it;
/** minimum signed value */
#if !defined(MIN8_8_I)
#define MIN8_8_I     (sint8_it)SCHAR_MIN
#endif
/** maximum signed value */
#if !defined(MAX8_8_I)
#define MAX8_8_I     (sint8_it)SCHAR_MAX
#endif
/** 8bit unsigned type */
typedef  unsigned char uint8_it;
/** minimum unsigned value */
#if !defined(UMIN8_8_I)
#define UMIN8_8_I    (uint8_it)0
#endif
/** maximum unsigned value */
#if !defined(UMAX8_8_I)
#define UMAX8_8_I    (uint8_it)UCHAR_MAX
#endif
#endif


/**************************************************************************************
  define 16 bit signed/unsigned types & constants
**************************************************************************************/

#if INT_MAX == 32767
/** 16bit signed type; the system type in this documentation might not
    reflect the definition on another target device; please see \ref
    basictypes and the source code */
typedef  int sint16_it;
/** minimum signed value */
#if !defined(MIN16_16_I)
#define MIN16_16_I     (sint16_it)INT_MIN
#endif
/** maximum signed value */
#if !defined(MAX16_16_I)
#define MAX16_16_I     (sint16_it)INT_MAX
#endif
/** 16bit unsigned type; the system type in this documentation might
    not reflect the definition on another target device; please see
    \ref basictypes and the source code */
typedef  unsigned int uint16_it;
/** minimum unsigned value */
#if !defined(UMIN16_16_I)
#define UMIN16_16_I    (uint16_it)0
#endif
/** maximum unsigned value */
#if !defined(UMAX16_16_I)
#define UMAX16_16_I    (uint16_it)UINT_MAX
#endif

#elif SHRT_MAX == 32767

typedef  short sint16_it;
#if !defined(MIN16_16_I)
#define MIN16_16_I     (sint16_it)SHRT_MIN
#endif
#if !defined(MAX16_16_I)
#define MAX16_16_I     (sint16_it)SHRT_MAX
#endif
typedef  unsigned short uint16_it;
#if !defined(UMIN16_16_I)
#define UMIN16_16_I    (uint16_it)0
#endif
#if !defined(UMAX16_16_I)
#define UMAX16_16_I    (uint16_it)USHRT_MAX
#endif

#elif SHRT_MAX == 8388607
typedef  short sint16_it;
#if !defined(MIN16_16_I)
#define MIN16_16_I     (sint16_it)-32768
#endif
#if !defined(MAX16_16_I)
#define MAX16_16_I     (sint16_it)32767
#endif
typedef  unsigned short uint16_it;
#if !defined(UMIN16_16_I)
#define UMIN16_16_I    (uint16_it)0
#endif
#if !defined(UMAX16_16_I)
#define UMAX16_16_I    (uint16_it)65535
#endif

#else
#error cannot find 16-bit type
#endif

/**************************************************************************************
  define 32 bit signed/unsigned types & constants
**************************************************************************************/

#if INT_MAX == 2147483647
/** 32bit signed type; the system type in this documentation might not
    reflect the definition on another target device; please see \ref
    basictypes and the source code */
typedef  int sint32_it;
/** minimum signed value */
#if !defined(MIN32_32_I)
#define MIN32_32_I     (sint32_it)INT_MIN
#endif
/** maximum signed value */
#if !defined(MAX32_32_I)
#define MAX32_32_I     (sint32_it)INT_MAX
#endif
/** 32bit unsigned type; the system type in this documentation might not
    reflect the definition on another target device; please see \ref
    basictypes and the source code */
typedef  unsigned int uint32_it;
/** minimum unsigned value */
#if !defined(UMIN32_32_I)
#define UMIN32_32_I    (uint32_it)0
#endif
/** maximum unsigned value */
#if !defined(UMAX32_32_I)
#define UMAX32_32_I    (uint32_it)UINT_MAX
#endif

#elif LONG_MAX == 2147483647

typedef  long sint32_it;
#if !defined(MIN32_32_I)
#define MIN32_32_I     (sint32_it)LONG_MIN
#endif
#if !defined(MAX32_32_I)
#define MAX32_32_I     (sint32_it)LONG_MAX
#endif
#ifndef _STDINT_H
typedef  unsigned long uint32_it;
#if !defined(UMIN32_32_I)
#define UMIN32_32_I    (uint32_it)0
#endif
#if !defined(UMAX32_32_I)
#define UMAX32_32_I    (uint32_it)ULONG_MAX
#endif
#endif

#else
#error cannot find 32-bit type
#endif

/**************************************************************************************
  float constants
**************************************************************************************/
#define FLOAT32_T_MAX_I (FLT_MAX)
#define FLOAT32_T_MIN_I (FLT_MIN)

/**************************************************************************************
   data type definitions with size and sign
**************************************************************************************/

typedef  char				char_it;	/* plain 8 bit character */
typedef  unsigned short		bool_it;	/* boolean 1 bit */
typedef  unsigned long long	uint64_it;	/* unsigned 64 bit integer */
typedef  long long			sint64_it;	/* signed 64 bit integer */
typedef  float				float32_it;	/* 32 bit floating point */
typedef  long double		float64_it;	/* 64 bit floating point */


typedef  struct{
    float32_it x;
    float32_it y;
}v2d_f32_it;


#endif /* INCLUSION_GUARDS_BT_BASIC_TYPES_H */

