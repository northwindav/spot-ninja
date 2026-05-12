# Spot-ninja#
An automation pipeline that will hopefully work. If it does, it will:
- Take as input a latitude longitude
- Retrieve high-resolution DEMs for a region, maybe 10 km x 10 km around that region
- Use Geomet to pull either HRDPS (1km or 2.5km) or GDPS wind fields required to initialize
- Initialize a WindNinja run

Provided that is all workable, future phases will include:
- Phase 2: Nudging by on-site weather

# Structure
The intent will be to make this as portable as possible for any user with moderate technical knowledge. To that end, we'll need to use a container to install WindNinja and to serve as the usual virtual environment

# Input
To start with, the only user input that will be required is a latitude and longitude within Canada. Technically, within the HRDPS Continental (2.5km) domain, but we'll say Canada

From that input, a Regional of Interest will be defined. We'll likely require some fine-tuning to get a balance of speed and accuracy, so to start it'll be about 10 km by 10 km. Beware of using approximation to degrees of lat and long, since the physical size of a degree of latitude changes dramatically within Canada.

The ROI will be used to retrieve high resolution DEM data, likely from an API available via the Geological Survey or somewhere within Canada's opendata.

We will then retrieve model forecast files. This part may be tricky since the servers provided within WindNinja default to mostly US models. https://github.com/firelab/windninja. It is likley that we'll have to build some calls to Geomet to pull canadian model data into a file, then configure those data to match the format, including naming, expected by WindNinja.

# Specific steps to get to production:
1. Examine WindNinja documentation to determine the folder structure expected, dependendices and such
2. Create a container to install WindNinja. This entire project could either run within the container, or if it makes sense, could just exchange information with WindNinja running in the container
3. Download and compile WindNinja into the container. This will again require reference to the documentation since there are a number of options. Ideally we'll want to have the option of running with STABILITY=on, while the GUI is a nice to have.
4. Create the project structure to take user location, download and if necessary restructure the DEM to match what is expected by WindNinja (documentation)
5. Create the project structure to download and if necessary restructure the HRDPS forecast data from Geomet
6. Choose some test cases and try running all of the above. Test cases should include areas with flat terrain (prairies), rolling terrain, mountainous terrain and extreme mountainous terrain (coast mountains of BC near the coast)
