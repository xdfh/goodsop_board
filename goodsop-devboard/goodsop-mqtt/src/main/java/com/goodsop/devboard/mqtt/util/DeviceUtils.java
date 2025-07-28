package com.goodsop.devboard.mqtt.util;

import lombok.extern.slf4j.Slf4j;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.NetworkInterface;
import java.util.Enumeration;

/**
 * 设备信息工具类
 */
@Slf4j
public class DeviceUtils {
    
    /**
     * 获取设备ID（CPU串号）
     * 
     * @return 设备ID
     */
    public static String getDeviceId() {
        String os = System.getProperty("os.name").toLowerCase();
        
        if (os.contains("win")) {
            return getWindowsCpuSerial();
        } else if (os.contains("linux")) {
            return getLinuxCpuSerial();
        } else {
            // 如果无法获取CPU串号，使用MAC地址作为备选
            return getMacAddress();
        }
    }
    
    /**
     * 获取Windows系统CPU串号
     *
     * @return CPU串号
     */
    private static String getWindowsCpuSerial() {
        // 首先尝试使用 wmic 命令
        try {
            Process process = Runtime.getRuntime().exec("wmic cpu get ProcessorId");
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            String line;
            while ((line = reader.readLine()) != null) {
                line = line.trim();
                if (!line.isEmpty() && !line.equals("ProcessorId")) {
                    return line;
                }
            }
        } catch (IOException e) {
            log.debug("wmic 命令不可用，尝试使用 PowerShell", e);
        }

        // 如果 wmic 失败，尝试使用 PowerShell
        try {
            Process process = Runtime.getRuntime().exec(new String[]{
                "powershell", "-Command", "Get-WmiObject -Class Win32_Processor | Select-Object -ExpandProperty ProcessorId"
            });
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            String line = reader.readLine();
            if (line != null && !line.trim().isEmpty()) {
                return line.trim();
            }
        } catch (IOException e) {
            log.debug("PowerShell 命令也失败，使用 MAC 地址作为设备 ID", e);
        }

        return getMacAddress();
    }
    
    /**
     * 获取Linux系统CPU串号
     * 
     * @return CPU串号
     */
    private static String getLinuxCpuSerial() {
        try {
            // 尝试从/proc/cpuinfo获取CPU序列号
            Process process = Runtime.getRuntime().exec("cat /proc/cpuinfo");
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            String line;
            while ((line = reader.readLine()) != null) {
                if (line.startsWith("Serial")) {
                    String[] parts = line.split(":");
                    if (parts.length > 1) {
                        return parts[1].trim();
                    }
                }
            }
            
            // 如果没有找到Serial，尝试获取processor id
            process = Runtime.getRuntime().exec("cat /proc/cpuinfo");
            reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            while ((line = reader.readLine()) != null) {
                if (line.startsWith("processor")) {
                    String[] parts = line.split(":");
                    if (parts.length > 1) {
                        return "CPU" + parts[1].trim();
                    }
                }
            }
        } catch (IOException e) {
            log.error("获取Linux CPU序列号失败", e);
        }
        return getMacAddress();
    }
    
    /**
     * 获取MAC地址作为设备标识
     * 
     * @return MAC地址
     */
    private static String getMacAddress() {
        try {
            Enumeration<NetworkInterface> networkInterfaces = NetworkInterface.getNetworkInterfaces();
            while (networkInterfaces.hasMoreElements()) {
                NetworkInterface networkInterface = networkInterfaces.nextElement();
                if (!networkInterface.isLoopback() && networkInterface.isUp()) {
                    byte[] mac = networkInterface.getHardwareAddress();
                    if (mac != null) {
                        StringBuilder sb = new StringBuilder();
                        for (int i = 0; i < mac.length; i++) {
                            sb.append(String.format("%02X", mac[i]));
                        }
                        return sb.toString();
                    }
                }
            }
        } catch (Exception e) {
            log.error("获取MAC地址失败", e);
        }
        
        // 如果都失败了，返回一个默认值
        return "UNKNOWN_DEVICE";
    }
    
    /**
     * 检测当前运行环境的设备型号
     * 
     * @return 设备型号
     */
    public static String detectDeviceModel() {
//        String os = System.getProperty("os.name").toLowerCase();
//
//        if (os.contains("linux")) {
//            try {
//                // 尝试从设备树或系统信息中获取设备型号
//                Process process = Runtime.getRuntime().exec("cat /proc/device-tree/model");
//                BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
//                String model = reader.readLine();
//                if (model != null && model.contains("RV1126")) {
//                    return "RV1126";
//                } else if (model != null && model.contains("RK3562")) {
//                    return "RK3562";
//                }
//            } catch (IOException e) {
//                log.debug("从设备树检测设备型号失败", e);
//            }
//        }
//
//        // 默认返回RK3562
//        return "RK3562";

        return "A10";
    }
}
