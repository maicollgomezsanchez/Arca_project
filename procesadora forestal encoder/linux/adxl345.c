
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <unistd.h>
#include <signal.h>
#include <time.h>

#include <sys/ioctl.h>
#include <linux/spi/spidev.h>

#define SPI_DEVICE "/dev/spidev0.0"
#define SPI_SPEED  1000000U

#define REG_DEVID       0x00
#define REG_BW_RATE     0x2C
#define REG_POWER_CTL   0x2D
#define REG_DATA_FORMAT 0x31
#define REG_DATAX0      0x32

#define ADXL345_ID      0xE5

static int spi_fd = -1;
static volatile sig_atomic_t running = 1;

static void stop_program(int sig)
{
    (void)sig;
    running = 0;
}

static int spi_transfer(uint8_t *tx, uint8_t *rx,
                        uint32_t length)
{
    struct spi_ioc_transfer tr = {0};

    tr.tx_buf = (uintptr_t)tx;
    tr.rx_buf = (uintptr_t)rx;
    tr.len = length;
    tr.speed_hz = SPI_SPEED;
    tr.bits_per_word = 8;

    return ioctl(spi_fd, SPI_IOC_MESSAGE(1), &tr);
}

static int read_register(uint8_t reg, uint8_t *value)
{
    uint8_t tx[2] = {
        (uint8_t)(reg | 0x80), 0x00
    };
    uint8_t rx[2] = {0};

    if (spi_transfer(tx, rx, 2) < 0)
        return -1;

    *value = rx[1];
    return 0;
}

static int write_register(uint8_t reg, uint8_t value)
{
    uint8_t tx[2] = {
        (uint8_t)(reg & 0x3F), value
    };
    uint8_t rx[2] = {0};

    return spi_transfer(tx, rx, 2) < 0 ? -1 : 0;
}

static int read_axes(int16_t *x, int16_t *y, int16_t *z)
{
    uint8_t tx[7] = {0};
    uint8_t rx[7] = {0};

    /* Lectura múltiple desde DATAX0 */
    tx[0] = REG_DATAX0 | 0xC0;

    if (spi_transfer(tx, rx, sizeof(tx)) < 0)
        return -1;

    *x = (int16_t)((uint16_t)rx[1] |
                   ((uint16_t)rx[2] << 8));

    *y = (int16_t)((uint16_t)rx[3] |
                   ((uint16_t)rx[4] << 8));

    *z = (int16_t)((uint16_t)rx[5] |
                   ((uint16_t)rx[6] << 8));

    return 0;
}

static int init_adxl345(void)
{
    uint8_t devid;

    if (read_register(REG_DEVID, &devid) < 0) {
        perror("Lectura DEVID");
        return -1;
    }

    printf("DEVID = 0x%02X\n", devid);

    if (devid != ADXL345_ID) {
        fprintf(stderr, "Error: ADXL345 no detectado\n");
        return -1;
    }

    /* Standby antes de configurar */
    if (write_register(REG_POWER_CTL, 0x00) < 0)
        return -1;

    /* 100 Hz */
    if (write_register(REG_BW_RATE, 0x0A) < 0)
        return -1;

    /* FULL_RES = 1, rango = +/-2 g */
    if (write_register(REG_DATA_FORMAT, 0x08) < 0)
        return -1;

    /* Measurement mode */
    if (write_register(REG_POWER_CTL, 0x08) < 0)
        return -1;

    return 0;
}

int main(void)
{
    struct sigaction sa = {0};
    sa.sa_handler = stop_program;
    sigemptyset(&sa.sa_mask);

    if (sigaction(SIGINT, &sa, NULL) < 0 ||
        sigaction(SIGTERM, &sa, NULL) < 0) {
        perror("sigaction");
        return EXIT_FAILURE;
    }

    spi_fd = open(SPI_DEVICE, O_RDWR);
    if (spi_fd < 0) {
        perror("open spidev");
        return EXIT_FAILURE;
    }

    uint8_t mode = SPI_MODE_3;
    uint8_t bits = 8;
    uint32_t speed = SPI_SPEED;

    if (ioctl(spi_fd, SPI_IOC_WR_MODE, &mode) < 0 ||
        ioctl(spi_fd, SPI_IOC_WR_BITS_PER_WORD, &bits) < 0 ||
        ioctl(spi_fd, SPI_IOC_WR_MAX_SPEED_HZ, &speed) < 0) {
        perror("Configuración SPI");
        close(spi_fd);
        return EXIT_FAILURE;
    }

    if (init_adxl345() < 0) {
        close(spi_fd);
        return EXIT_FAILURE;
    }

    printf("ADXL345 iniciado. Ctrl+C para salir.\n");

    while (running) {
        int16_t x, y, z;

        if (read_axes(&x, &y, &z) < 0) {
            perror("Lectura de ejes");
            break;
        }

        /*
         * En FULL_RES la sensibilidad nominal es
         * aproximadamente 3.9 mg/LSB.
         */
        const float scale = 0.0039f;

        printf("X: %7.3f g | Y: %7.3f g | Z: %7.3f g\n",
               x * scale, y * scale, z * scale);

        fflush(stdout);

        struct timespec delay = {
            .tv_sec = 0,
            .tv_nsec = 100000000L
        };

        while (nanosleep(&delay, &delay) < 0 &&
               errno == EINTR && running) {
        }
    }

    close(spi_fd);
    printf("\nPrograma terminado.\n");

    return EXIT_SUCCESS;
}
