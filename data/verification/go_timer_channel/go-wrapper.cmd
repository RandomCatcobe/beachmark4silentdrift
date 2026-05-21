@echo off
if "%GO_ADAPTER_VERSION%"=="1.22" set GODEBUG=asynctimerchan=1
if "%GO_ADAPTER_VERSION%"=="1.23" set GODEBUG=asynctimerchan=0
go %*
