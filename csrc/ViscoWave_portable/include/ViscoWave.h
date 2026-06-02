// ViscoWave.h

#ifndef VISCOWAVE_H
#define VISCOWAVE_H

#if defined(_WIN32) || defined(__CYGWIN__)
  #ifdef VISCOWAVE_BUILD
    #define VISCOWAVE_API __declspec(dllexport)
  #else
    #define VISCOWAVE_API __declspec(dllimport)
  #endif
#else
  #if defined(__GNUC__) && __GNUC__ >= 4
    #define VISCOWAVE_API __attribute__((visibility("default")))
  #else
    #define VISCOWAVE_API
  #endif
#endif

#ifdef __cplusplus
extern "C" {
#endif

// Returns ViscoWave Deflections
VISCOWAVE_API int ViscoWave(double* displacement, double* Sigmoid, double* Pavement,
					double Load_Pressure, double Load_Radius, double* Sensor_Location, double* Time,
					double* Timehistory, double dt, int num_prony_elements, int Num_Pavt_Layers, int Num_Sensors, 
					int Num_Time, int Num_VE_Layer);

#ifdef __cplusplus
}
#endif

#endif
