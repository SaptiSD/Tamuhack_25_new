fetch("/static/data/nyc_schools_energy_dynamodb.json")
 .then((response) => {
   if (!response.ok) {
     throw new Error("Network response was not ok " + response.statusText);
   }
   return response.json();
 })
 .then((data) => {
   const boroughData = {
     Manhattan: { totalUsage: 0, count: 0 },
     Brooklyn: { totalUsage: 0, count: 0 },
     Queens: { totalUsage: 0, count: 0 },
     Bronx: { totalUsage: 0, count: 0 },
     StatenIsland: { totalUsage: 0, count: 0 },
   };


   // Process the data and populate boroughData
   data.forEach((school) => {
     const { Borough, TotalUsage } = school;
     if (boroughData[Borough]) {
       boroughData[Borough].totalUsage += TotalUsage;
       boroughData[Borough].count++;
     }
   });


   // Log processed data for verification (optional)
   console.log("Processed Borough Data:", boroughData);


   // Expose the processed data for use in other scripts
   window.boroughData = boroughData;
 })
 .catch((error) => console.error("Fetch error:", error));