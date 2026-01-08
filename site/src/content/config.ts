import { defineCollection, z } from 'astro:content';

const packages = defineCollection({
    type: 'content',
    schema: z.object({
        title: z.string(),
        version: z.string(),
        description: z.string(),
        latest: z.boolean().optional(),
        keywords: z.string().optional(),
        homepage: z.string().optional(),
        license: z.string().optional(),
        searchIndex: z.string().optional(),
        dependencies: z.array(z.string()).optional(),
    }),
});

export const collections = { packages };
