import { db } from "./server/db";
import { materials } from "./shared/schema";

async function seed() {
  const allMaterials = await db.select().from(materials);
  if (allMaterials.length === 0) {
    console.log("Seeding example materials...");
    await db.insert(materials).values([
      {
        title: "Introduction to Photosynthesis",
        type: "text",
        content: `Photosynthesis is a process used by plants and other organisms to convert light energy into chemical energy that, through cellular respiration, can later be released to fuel the organism's activities. This chemical energy is stored in carbohydrate molecules, such as sugars and starches, which are synthesized from carbon dioxide and water.
        
In most cases, oxygen is also released as a waste product. Most plants, algae, and cyanobacteria perform photosynthesis; such organisms are called photoautotrophs. Photosynthesis is largely responsible for producing and maintaining the oxygen content of the Earth's atmosphere, and supplies most of the energy necessary for life on Earth.

The process always begins when energy from light is absorbed by proteins called reaction centers that contain green chlorophyll pigments. In plants, these proteins are held inside organelles called chloroplasts, which are most abundant in leaf cells, while in bacteria they are embedded in the plasma membrane.
        `
      },
      {
        title: "Newton's Laws of Motion",
        type: "text",
        content: `Newton's laws of motion are three physical laws that, together, laid the foundation for classical mechanics. They describe the relationship between a body and the forces acting upon it, and its motion in response to those forces.

First law: In an inertial frame of reference, an object either remains at rest or continues to move at a constant velocity, unless acted upon by a net force.
Second law: In an inertial reference frame, the vector sum of the forces F on an object is equal to the mass m of that object multiplied by the acceleration a of the object: F = ma.
Third law: When one body exerts a force on a second body, the second body simultaneously exerts a force equal in magnitude and opposite in direction on the first body.
        `
      }
    ]);
    console.log("Seeded successfully.");
  } else {
    console.log("Database already contains materials, skipping seed.");
  }
  process.exit(0);
}

seed().catch((err) => {
  console.error(err);
  process.exit(1);
});
