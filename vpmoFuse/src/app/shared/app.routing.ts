import { RouterModule } from '@angular/router';
import { NgModule } from '@angular/core';

import { HomeComponent } from '../home/home.component';
import { ErrorComponent } from '../error/error.component';

const ROUTES = [
    { path: 'home', component: HomeComponent },
    { path: '', redirectTo: 'home', pathMatch: 'full' },
    { path: '**', component: ErrorComponent },
];

@NgModule({
    imports: [
        RouterModule.forRoot(ROUTES)
    ],
    exports: [
        RouterModule
    ]
})
export class AppRoutingModule {}
