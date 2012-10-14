//  Copyright (c) 2012 Fredrik Mellbin
//
//  Permission is hereby granted, free of charge, to any person obtaining a copy
//  of this software and associated documentation files (the "Software"), to deal
//  in the Software without restriction, including without limitation the rights
//  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
//  copies of the Software, and to permit persons to whom the Software is
//  furnished to do so, subject to the following conditions:
//
//  The above copyright notice and this permission notice shall be included in
//  all copies or substantial portions of the Software.
//
//  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
//  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
//  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
//  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
//  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
//  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
//  THE SOFTWARE.

#ifndef VSHELPER_H
#define VSHELPER_H

#include <stdlib.h>
#include <stdint.h>
#include "VapourSynth.h"

// VS2010 doesn't recognize inline in c mode
#if defined(_MSC_VER) && !defined(__cplusplus)
#define inline _inline
#endif

#ifdef _WIN32
#define VS_ALIGNED_MALLOC(pptr, size, alignment) *(pptr) = _aligned_malloc((size), (alignment))
#define VS_ALIGNED_FREE(ptr) _aligned_free((ptr))
#else
#define VS_ALIGNED_MALLOC(pptr, size, alignment) posix_memalign((pptr), (alignment), (size))
#define VS_ALIGNED_FREE(ptr) free((ptr))
#endif

#ifdef __cplusplus
// A nicer templated malloc for all the C++ users out there
template<class T>
static inline T* vs_aligned_malloc(size_t size, size_t alignment) {
#ifdef _WIN32
	return (T*)_aligned_malloc(size, alignment);
#else
	void *tmp;
	if (posix_memalign(&tmp, alignment, size))
		tmp = 0;
	return (T*)tmp;
#endif
}

static inline void vs_aligned_free(void *ptr) {
	VS_ALIGNED_FREE(ptr);
}
#endif //__cplusplus

// convenience function for checking if the format never changes between frames
static inline int isConstantFormat(const VSVideoInfo *vi) {
    return vi->height > 0 && vi->width > 0 && vi->format;
}

// convenience function to check for if two clips have the same format (unknown/changeable will be considered the same too)
static inline int isSameFormat(const VSVideoInfo *v1, const VSVideoInfo *v2) {
    return v1->height == v2->height && v1->width == v2->width && v1->format == v2->format;
}

// multiplies and divides a rational number, such as a frame duration, in place and reduces the result
// returns non-zero value on overflow
static inline int muldivRational(int64_t *num, int64_t *den, int64_t mul, int64_t div) {
    *num *= mul;
    *den *= div;
}

// converts an int64 to int with saturation, useful to silence warnings when reading int properties among other things
static inline int int64ToIntS(int64_t i) {
    if (i > INT_MAX)
        return INT_MAX;
    else if (i < INT_MIN)
        return INT_MIN;
    else return (int)i;
}

#endif
