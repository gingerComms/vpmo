import { BrowserModule } from '@angular/platform-browser';
import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { RouterModule, Routes } from '@angular/router';

import { UserComponent } from './user.component';
// import { AdminMenuComponent } from './adminMenu/admin-menu.component';
import { LoginModule } from './login-2/login.module';
import { SignUpComponent } from './signUp/sign-up.component';
import { UserService } from './user.service';
import { HttpClientModule } from '@angular/common/http';
import { AuthenticationService } from '../_services/authentication.service';
import { AuthGuard } from '../_guards/auth.guard';
import { DashboardComponent } from './dashboard/dashboard.component';
import { UserProfileComponent } from './profile/userProfile.component';

const UserRoutes: Routes = [
    {
        path: 'user',
        component: UserComponent,
        children: [
            // { path: 'login', component: LoginComponent },
            { path: 'signup', component: SignUpComponent },
            { path: 'dashboard', component: DashboardComponent },
            { path: 'profile', component: UserProfileComponent }
            // { path: '', component: AdminMenuComponent, canActivate: [UserService] }
        ]
    },
];

@NgModule({
    imports: [
        BrowserModule,
        CommonModule,
        FormsModule,
        ReactiveFormsModule,
        RouterModule.forChild(UserRoutes),
        HttpClientModule,
        LoginModule,
    ],
    exports: [
        RouterModule,
        SignUpComponent,
        DashboardComponent,
        UserProfileComponent,
    ],
    declarations: [
        UserComponent,
        SignUpComponent,
        DashboardComponent,
        UserProfileComponent,

    ],
    providers: [
        UserService,
        AuthenticationService,
        AuthGuard,
    ],
    schemas: [
        CUSTOM_ELEMENTS_SCHEMA,
    ]
})

export class UserModule {}
