
#ifndef _MLT_v2_H
#define _MLT_v2_H

double MLTConvert_v2(int yr, int mo, int dy, int hr, int mt ,int sc,
		     double mlon, char *igrf_filename);
double MLTConvertYMDHMS_v2(int yr, int mo, int dy, int hr, int mt, int sc,
			   double mlon, char *igrf_filename);
double MLTConvertYrsec_v2(int yr, int yrsec, double mlon, char *igrf_filename);
double MLTConvertEpoch_v2(double epoch, double mlon, char *igrf_filename);

#endif

