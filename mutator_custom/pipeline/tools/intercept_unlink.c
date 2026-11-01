// intercept_unlink.c —— 拦截 unlink/unlinkat/remove，在 .merge 控制文件被删除前复制保存
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dlfcn.h>
#include <unistd.h>
#include <fcntl.h>

static void save_file(const char *path) {
    if (!path) return;
    // 只抢救 merge 控制文件
    if (!strstr(path, ".merge") && !strstr(path, "merge.txt")) return;
    const char *dir = getenv("MERGE_CAPTURE_DIR");
    if (!dir) dir = "/tmp/merge_capture";
    const char *base = strrchr(path, '/');
    base = base ? base + 1 : path;
    static int counter = 0;
    char dest[1024];
    snprintf(dest, sizeof(dest), "%s/%d_%d_%s",
             dir, (int)getpid(), counter++, base);
    int src = open(path, O_RDONLY);
    if (src < 0) return;
    int dst = open(dest, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (dst >= 0) {
        char buf[16384];
        ssize_t n;
        while ((n = read(src, buf, sizeof(buf))) > 0)
            if (write(dst, buf, n) != n) break;
        close(dst);
    }
    close(src);
}

int unlink(const char *path) {
    save_file(path);
    static int (*real_unlink)(const char *) = NULL;
    if (!real_unlink) real_unlink = dlsym(RTLD_NEXT, "unlink");
    return real_unlink(path);
}

int unlinkat(int dirfd, const char *path, int flags) {
    save_file(path);
    static int (*real_unlinkat)(int, const char *, int) = NULL;
    if (!real_unlinkat) real_unlinkat = dlsym(RTLD_NEXT, "unlinkat");
    return real_unlinkat(dirfd, path, flags);
}

int remove(const char *path) {
    save_file(path);
    static int (*real_remove)(const char *) = NULL;
    if (!real_remove) real_remove = dlsym(RTLD_NEXT, "remove");
    return real_remove(path);
}
