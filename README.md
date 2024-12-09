ISYS-5021 150M Data Parser
==========================

This repository contains a **CLI** and a **GUI** implementation for parsing radar data from the **ISYS-5021 Radar System**. Both versions read radar data packets, validate checksums, and display parsed target details, including signal strength, range, velocity, direction, and azimuth.

Repository Structure
--------------------
#### CLI implementation
 `├── ISYS_5021_150M_CLI.py`        
#### Folder containing GUI implementation      
    `└── ISYS_150M_GUI`                
#### Main entry point for the GUI      
    `├── main.py`                  
#### GUI design and functionality      
    `├── gui.py`                   
#### Handles saving/loading data      
    `├── data_manager.py`          
#### Manages radar socket connection  
    `└── socket_manager.py`  

Features
--------

*   Parse and validate radar data packets.
    
*   Extract and display:
    
    *   Frame ID
        
    *   Signal Strength (dB)
        
    *   Range (m)
        
    *   Velocity (m/s) with direction (Incoming/Outgoing/Static)
        
    *   Azimuth angle (°)
        
*   **CLI Version**:
    
    *   Displays parsed results in the terminal.
        
*   **GUI Version**:
    
    *   Interactive interface for starting/stopping the server.
        
    *   Displays target data in a formatted table.
        
    *   Save parsed data to JSON.
        
    *   View historical data by Frame ID.
        

Usage
-----

### CLI Version

1.  `python ISYS\_5021\_150M\_CLI.py`
    
2.  View the parsed radar data directly in the terminal.
    

### GUI Version

1.  `cd ISYS\_150M\_GUI`
    
2.  `python main.py`
    
3.  Use the interactive interface:
    
    *   **Connect**: Start listening to radar data.
        
    *   **Disconnect**: Stop listening.
        
    *   **Save to JSON**: Save parsed data.
        
    *   **View Historical Data**: View previous frames using Frame IDs.
        

Notes
-----

*   Ensure the radar device is configured to send data to the specified IP and port.
    
*   Adjust IP and port settings in the scripts as needed. Default settings:
    
    *   IP: 192.168.252.2
        
    *   Port: 2050
        
*   Data parsing is based on the ISYS-5021 radar documentation. Ensure compatibility with the radar's output format.