// SPDX-License-Identifier: Apache-2.0
//
// Shim for qua-legacy-text and qua-legacy-usx-check: one call compresses a
// string with every preset of Unishox2. The tool compiles this file
// together with unishox2.c of the submodule 3rdparty/Unishox2. It includes
// the public header of the library and holds no code of it.
//
// Build flag: -DUNISHOX_API_WITH_OUTPUT_LEN=1, so that the library checks
// the length of the output buffer.
#include <string.h>

#include "unishox2.h"

#define QUA_USX_BUF 4096

#define QUA_USX_PRESETS(X) \
    X(0, DFLT) X(1, ALPHA_ONLY) X(2, ALPHA_NUM_ONLY) X(3, ALPHA_NUM_SYM_ONLY) \
    X(4, ALPHA_NUM_SYM_ONLY_TXT) X(5, FAVOR_ALPHA) X(6, FAVOR_DICT) X(7, FAVOR_SYM) \
    X(8, FAVOR_UMLAUT) X(9, NO_DICT) X(10, NO_UNI) X(11, NO_UNI_FAVOR_TEXT) \
    X(12, URL) X(13, JSON) X(14, JSON_NO_UNI) X(15, XML) X(16, HTML)

int qua_usx_count(void) { return 17; }

const char *qua_usx_name(int preset) {
    switch (preset) {
#define X(i, name) case i: return #name;
        QUA_USX_PRESETS(X)
#undef X
    }
    return "";
}

static int compress(int preset, const char *in, int len, char *out, int olen) {
    switch (preset) {
#define X(i, name) case i: return unishox2_compress(in, len, out, olen, USX_PSET_##name);
        QUA_USX_PRESETS(X)
#undef X
    }
    return -1;
}

static int decompress(int preset, const char *in, int len, char *out, int olen) {
    switch (preset) {
#define X(i, name) case i: return unishox2_decompress(in, len, out, olen, USX_PSET_##name);
        QUA_USX_PRESETS(X)
#undef X
    }
    return -1;
}

// Compress in[0..len) with every preset. lens[i] is the length of the
// compressed bytes of preset i. It is -1 if the output does not fit the
// buffer, and -2 if the decompressed bytes are not the input.
void qua_usx_all(const char *in, int len, int *lens) {
    char packed[QUA_USX_BUF];
    char back[QUA_USX_BUF];
    for (int i = 0; i < 17; i++) {
        int n = compress(i, in, len, packed, QUA_USX_BUF);
        if (n < 0 || n > QUA_USX_BUF) {
            lens[i] = -1;
            continue;
        }
        int m = decompress(i, packed, n, back, QUA_USX_BUF);
        lens[i] = (m == len && memcmp(in, back, (size_t)len) == 0) ? n : -2;
    }
}

// The default preset alone, for qua-legacy-usx-check. Each returns the value of
// the library call.
int qua_usx_dflt_compress(const char *in, int len, char *out, int olen) {
    return unishox2_compress(in, len, out, olen, USX_PSET_DFLT);
}

int qua_usx_dflt_decompress(const char *in, int len, char *out, int olen) {
    return unishox2_decompress(in, len, out, olen, USX_PSET_DFLT);
}
