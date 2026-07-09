import { CssReset, CssVariables } from '@dhis2/ui'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { createHashRouter, Outlet, RouterProvider } from 'react-router-dom'
import { Layout } from '@/components/layout/Layout'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { CreateRolePage } from '@/pages/CreateRolePage'
import { UpdateRolePage } from '@/pages/UpdateRolePage'
import { SyncUrlWithGlobalShell } from '@/utils/SyncUrlWithGlobalShell'

const queryClient = new QueryClient()

const router = createHashRouter([
    {
        element: <SyncUrlWithGlobalShell />,
        children: [
            {
                element: <Layout />,
                children: [
                    {
                        element: (
                            <PageWrapper>
                                <Outlet />
                            </PageWrapper>
                        ),
                        children: [
                            { path: '/', element: <CreateRolePage /> },
                            { path: '/update', element: <UpdateRolePage /> },
                        ],
                    },
                ],
            },
        ],
    },
])

const App = () => (
    <QueryClientProvider client={queryClient}>
        <CssReset />
        <CssVariables theme spacers colors elevations />
        <RouterProvider router={router} />
    </QueryClientProvider>
)

export default App
