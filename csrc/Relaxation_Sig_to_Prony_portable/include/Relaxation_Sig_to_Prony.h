// Relaxation_Sig_to_Prony.h

#ifndef RELAXATION_SIG_TO_PRONY_H
#define RELAXATION_SIG_TO_PRONY_H

#if defined(_WIN32) || defined(__CYGWIN__)
  #ifdef RELAXATION_SIG_TO_PRONY_BUILD
    #define RELAXATION_SIG_TO_PRONY_API __declspec(dllexport)
  #else
    #define RELAXATION_SIG_TO_PRONY_API __declspec(dllimport)
  #endif
#else
  #if defined(__GNUC__) && __GNUC__ >= 4
    #define RELAXATION_SIG_TO_PRONY_API __attribute__((visibility("default")))
  #else
    #define RELAXATION_SIG_TO_PRONY_API
  #endif
#endif

#ifdef __cplusplus
extern "C" {
#endif

// Returns Prony Coefficients from Sigmoidal Coefficients for Relaxation Modulus
RELAXATION_SIG_TO_PRONY_API int Relaxation_Sig_to_Prony(double* Prony, double* Sigmoid, int Num_Sigmoid);

#ifdef __cplusplus
}
#endif

#endif
